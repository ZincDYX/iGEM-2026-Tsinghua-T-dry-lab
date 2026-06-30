"""Two-phase, mass-conserving enzyme-cascade model.

The state variables are cell-averaged concentrations. Rapid partition equilibrium
is assumed within each ODE evaluation. This prevents the common error of simply
multiplying Vmax by an enrichment factor without accounting for condensate volume.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class CascadeParameters:
    phi: float = 0.05
    oc_total: float = 1.0
    dmt_total: float = 1.0
    kcat_oc: float = 1.0
    km_oc: float = 1.0
    kcat_dmt: float = 1.0
    km_dmt: float = 1.0
    partition_oc: float = 50.0
    partition_dmt: float = 50.0
    partition_a: float = 5.0
    partition_b: float = 5.0
    partition_product: float = 1.0
    activity_ratio_oc: float = 1.0
    activity_ratio_dmt: float = 1.0
    kdeg_b: float = 0.0
    kdeg_product: float = 0.0

    def validate(self) -> None:
        if not 0.0 <= self.phi <= 1.0:
            raise ValueError("phi must be between 0 and 1")
        nonnegative = (
            self.oc_total,
            self.dmt_total,
            self.kcat_oc,
            self.km_oc,
            self.kcat_dmt,
            self.km_dmt,
            self.kdeg_b,
            self.kdeg_product,
        )
        if any(value < 0 for value in nonnegative):
            raise ValueError("concentrations and kinetic parameters must be nonnegative")
        partitions = (
            self.partition_oc,
            self.partition_dmt,
            self.partition_a,
            self.partition_b,
            self.partition_product,
        )
        if any(value <= 0 for value in partitions):
            raise ValueError("partition coefficients must be positive")


@dataclass(frozen=True)
class SimulationResult:
    time: np.ndarray
    concentrations: np.ndarray

    @property
    def substrate(self) -> np.ndarray:
        return self.concentrations[0]

    @property
    def intermediate(self) -> np.ndarray:
        return self.concentrations[1]

    @property
    def product(self) -> np.ndarray:
        return self.concentrations[2]


def phase_concentrations(average: float, partition: float, phi: float) -> tuple[float, float]:
    """Return dense- and dilute-phase concentrations under mass conservation."""
    denominator = (1.0 - phi) + phi * partition
    dilute = average / denominator
    dense = partition * dilute
    return dense, dilute


def _mm_rate(enzyme: float, substrate: float, kcat: float, km: float) -> float:
    if substrate <= 0 or enzyme <= 0 or kcat <= 0:
        return 0.0
    return kcat * enzyme * substrate / (km + substrate)


def cascade_rates(state: np.ndarray, params: CascadeParameters) -> tuple[float, float]:
    a, b, _product = np.maximum(state, 0.0)
    phi = params.phi

    oc_in, oc_out = phase_concentrations(params.oc_total, params.partition_oc, phi)
    dmt_in, dmt_out = phase_concentrations(params.dmt_total, params.partition_dmt, phi)
    a_in, a_out = phase_concentrations(a, params.partition_a, phi)
    b_in, b_out = phase_concentrations(b, params.partition_b, phi)

    v1_in = _mm_rate(oc_in, a_in, params.kcat_oc * params.activity_ratio_oc, params.km_oc)
    v1_out = _mm_rate(oc_out, a_out, params.kcat_oc, params.km_oc)
    v2_in = _mm_rate(dmt_in, b_in, params.kcat_dmt * params.activity_ratio_dmt, params.km_dmt)
    v2_out = _mm_rate(dmt_out, b_out, params.kcat_dmt, params.km_dmt)

    v1 = phi * v1_in + (1.0 - phi) * v1_out
    v2 = phi * v2_in + (1.0 - phi) * v2_out
    return v1, v2


def simulate_cascade(
    params: CascadeParameters,
    initial: tuple[float, float, float] = (10.0, 0.0, 0.0),
    t_end: float = 24.0,
    points: int = 241,
) -> SimulationResult:
    params.validate()
    if t_end <= 0 or points < 2:
        raise ValueError("t_end must be positive and points must be at least 2")

    def rhs(_time: float, state: np.ndarray) -> np.ndarray:
        v1, v2 = cascade_rates(state, params)
        _a, b, product = np.maximum(state, 0.0)
        return np.array(
            [-v1, v1 - v2 - params.kdeg_b * b, v2 - params.kdeg_product * product]
        )

    evaluation_times = np.linspace(0.0, t_end, points)
    solution = solve_ivp(
        rhs,
        (0.0, t_end),
        np.asarray(initial, dtype=float),
        t_eval=evaluation_times,
        method="LSODA",
        rtol=1e-8,
        atol=1e-10,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    concentrations = np.maximum(solution.y, 0.0)
    return SimulationResult(solution.t, concentrations)
