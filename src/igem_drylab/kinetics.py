"""Two-phase, mass-conserving enzyme-cascade model.

The state variables are cell-averaged concentrations. Rapid partition equilibrium
is assumed within each ODE evaluation. This prevents the common error of simply
multiplying Vmax by an enrichment factor without accounting for condensate volume.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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
class CompetitiveCascadeParameters:
    """Parameters for OC-first/DMT-later competitive cascade simulation.

    State variables are cell-averaged concentrations:
    A = upstream substrate for OC and off-path DMT reaction,
    B = OC product / desired DMT substrate,
    P = final target product,
    Q = DMT leakage byproduct.
    """

    phi: float = 0.05
    oc_total: float = 1.0
    dmt_total: float = 1.0
    kcat_oc: float = 1.0
    km_oc: float = 1.0
    kcat_dmt_product: float = 1.0
    km_dmt_product: float = 1.0
    kcat_dmt_leak: float = 0.3
    km_dmt_leak: float = 1.0
    partition_oc: float = 50.0
    partition_dmt: float = 50.0
    partition_a: float = 5.0
    partition_b: float = 5.0
    partition_product: float = 1.0
    partition_byproduct: float = 1.0
    activity_ratio_oc: float = 1.0
    activity_ratio_dmt: float = 1.0
    kdeg_a: float = 0.0
    kdeg_b: float = 0.0
    kdeg_product: float = 0.0
    kdeg_byproduct: float = 0.0

    def validate(self) -> None:
        if not 0.0 <= self.phi <= 1.0:
            raise ValueError("phi must be between 0 and 1")
        nonnegative = (
            self.oc_total,
            self.dmt_total,
            self.kcat_oc,
            self.km_oc,
            self.kcat_dmt_product,
            self.km_dmt_product,
            self.kcat_dmt_leak,
            self.km_dmt_leak,
            self.kdeg_a,
            self.kdeg_b,
            self.kdeg_product,
            self.kdeg_byproduct,
        )
        if any(value < 0 for value in nonnegative):
            raise ValueError("concentrations and kinetic parameters must be nonnegative")
        partitions = (
            self.partition_oc,
            self.partition_dmt,
            self.partition_a,
            self.partition_b,
            self.partition_product,
            self.partition_byproduct,
        )
        if any(value <= 0 for value in partitions):
            raise ValueError("partition coefficients must be positive")
        if self.km_oc == 0 or self.km_dmt_product == 0 or self.km_dmt_leak == 0:
            raise ValueError("Km values must be positive")


@dataclass(frozen=True)
class InductionGate:
    """Expression/activity gate used for piecewise induction.

    mode="step" is intentionally handled by segmented ODE integration so the
    solver never steps across a discontinuity blindly.
    """

    on_time: float = 0.0
    off_time: float | None = None
    basal: float = 0.0
    induced: float = 1.0
    mode: str = "step"
    transition_width: float = 0.25

    def validate(self) -> None:
        if self.on_time < 0:
            raise ValueError("on_time must be nonnegative")
        if not all(np.isfinite(value) for value in (self.on_time, self.basal, self.induced, self.transition_width)) or (self.off_time is not None and not np.isfinite(self.off_time)):
            raise ValueError("induction_gate_values_must_be_finite")
        if self.off_time is not None and self.off_time <= self.on_time:
            raise ValueError("off_time must be greater than on_time")
        if self.basal < 0 or self.induced < 0:
            raise ValueError("gate levels must be nonnegative")
        if self.mode not in {"step", "sigmoid"}:
            raise ValueError("mode must be 'step' or 'sigmoid'")
        if self.transition_width <= 0:
            raise ValueError("transition_width must be positive")


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


@dataclass(frozen=True)
class CompetitiveSimulationResult:
    time: np.ndarray
    concentrations: np.ndarray
    oc_gate: np.ndarray
    dmt_gate: np.ndarray

    @property
    def substrate(self) -> np.ndarray:
        return self.concentrations[0]

    @property
    def intermediate(self) -> np.ndarray:
        return self.concentrations[1]

    @property
    def product(self) -> np.ndarray:
        return self.concentrations[2]

    @property
    def byproduct(self) -> np.ndarray:
        return self.concentrations[3]


@dataclass(frozen=True)
class GlabridinKineticParameters:
    """Explicit two-phase parameters for 9→10→11→15 and competing 9→13.

    Units must be internally consistent. Values are deliberately required at
    construction: callers must obtain them from reviewed parameter records or
    explicitly labelled assumptions outside this numerical module.
    """
    phi: float
    pt_total: float
    oc_total: float
    dmt_total: float
    kcat_pt: float
    km_pt: float
    kcat_oc: float
    km_oc: float
    kcat_dmt_9: float
    km_dmt_9: float
    kcat_dmt_11: float
    km_dmt_11: float
    partition_pt: float
    partition_oc: float
    partition_dmt: float
    partition_9: float
    partition_10: float
    partition_11: float
    activity_dense_pt: float
    activity_dilute_pt: float
    activity_dense_oc: float
    activity_dilute_oc: float
    activity_dense_dmt: float
    activity_dilute_dmt: float
    # Deprecated compatibility aliases; production equations do not consume them.
    partition_13: float = 1.0
    partition_15: float = 1.0
    kdeg_9: float = 0.0
    kdeg_10: float = 0.0
    kdeg_11: float = 0.0
    kdeg_13: float = 0.0
    kdeg_15: float = 0.0

    def validate(self) -> None:
        if not 0 <= self.phi <= 1:
            raise ValueError("phi must be between 0 and 1")
        values = tuple(self.__dict__.values())
        if any(value < 0 for value in values):
            raise ValueError("glabridin parameters must be nonnegative")
        if any(value == 0 for value in (self.km_pt, self.km_oc, self.km_dmt_9, self.km_dmt_11)):
            raise ValueError("Km values must be positive")
        if any(value <= 0 for value in (self.partition_pt, self.partition_oc, self.partition_dmt, self.partition_9, self.partition_10, self.partition_11)):
            raise ValueError("partition coefficients must be positive")


@dataclass(frozen=True)
class GlabridinSimulationResult:
    time: np.ndarray
    concentrations: np.ndarray
    pt_gate: np.ndarray
    oc_gate: np.ndarray
    dmt_gate: np.ndarray
    degradation_loss: float = 0.0

    @property
    def x9(self) -> np.ndarray: return self.concentrations[0]
    @property
    def x10(self) -> np.ndarray: return self.concentrations[1]
    @property
    def x11(self) -> np.ndarray: return self.concentrations[2]
    @property
    def x13(self) -> np.ndarray: return self.concentrations[3]
    @property
    def x15(self) -> np.ndarray: return self.concentrations[4]

    @property
    def mass_balance_error(self) -> float:
        """Numerical conservation residual after subtracting modeled sinks."""
        total = self.concentrations.sum(axis=0)
        return abs(float((total[0] - total[-1]) - self.degradation_loss))

    @property
    def modeled_degradation_loss(self) -> float:
        """Net pathway mass removed by enabled first-order degradation sinks."""
        return self.degradation_loss


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


def gate_value(time: float, gate: InductionGate) -> float:
    gate.validate()
    if gate.mode == "step":
        active = time >= gate.on_time and (gate.off_time is None or time < gate.off_time)
        return gate.induced if active else gate.basal
    on = 1.0 / (1.0 + np.exp(-(time - gate.on_time) / gate.transition_width))
    if gate.off_time is None:
        active_fraction = on
    else:
        off = 1.0 / (1.0 + np.exp(-(time - gate.off_time) / gate.transition_width))
        active_fraction = on * (1.0 - off)
    return float(gate.basal + (gate.induced - gate.basal) * active_fraction)


def competitive_dmt_rates(
    *,
    dmt: float,
    substrate_a: float,
    intermediate_b: float,
    kcat_product: float,
    km_product: float,
    kcat_leak: float,
    km_leak: float,
) -> tuple[float, float]:
    """Return DMT rates for B->P and competing A->Q.

    The two substrates share one DMT enzyme pool. This is the standard
    rapid-equilibrium multi-substrate Michaelis-Menten denominator:
    v_i = kcat_i * E * (S_i / Km_i) / (1 + sum_j S_j/Km_j).
    """
    if dmt <= 0:
        return 0.0, 0.0
    a = max(substrate_a, 0.0)
    b = max(intermediate_b, 0.0)
    denom = 1.0 + a / km_leak + b / km_product
    if denom <= 0:
        return 0.0, 0.0
    v_product = kcat_product * dmt * (b / km_product) / denom
    v_leak = kcat_leak * dmt * (a / km_leak) / denom
    return v_product, v_leak


def competitive_cascade_rates(
    state: np.ndarray,
    params: CompetitiveCascadeParameters,
    *,
    oc_gate_level: float,
    dmt_gate_level: float,
) -> tuple[float, float, float]:
    a, b, _product, _byproduct = np.maximum(state, 0.0)
    phi = params.phi

    oc_total = params.oc_total * oc_gate_level
    dmt_total = params.dmt_total * dmt_gate_level

    oc_in, oc_out = phase_concentrations(oc_total, params.partition_oc, phi)
    dmt_in, dmt_out = phase_concentrations(dmt_total, params.partition_dmt, phi)
    a_in, a_out = phase_concentrations(a, params.partition_a, phi)
    b_in, b_out = phase_concentrations(b, params.partition_b, phi)

    v_oc_in = _mm_rate(oc_in, a_in, params.kcat_oc * params.activity_ratio_oc, params.km_oc)
    v_oc_out = _mm_rate(oc_out, a_out, params.kcat_oc, params.km_oc)
    v_product_in, v_leak_in = competitive_dmt_rates(
        dmt=dmt_in,
        substrate_a=a_in,
        intermediate_b=b_in,
        kcat_product=params.kcat_dmt_product * params.activity_ratio_dmt,
        km_product=params.km_dmt_product,
        kcat_leak=params.kcat_dmt_leak * params.activity_ratio_dmt,
        km_leak=params.km_dmt_leak,
    )
    v_product_out, v_leak_out = competitive_dmt_rates(
        dmt=dmt_out,
        substrate_a=a_out,
        intermediate_b=b_out,
        kcat_product=params.kcat_dmt_product,
        km_product=params.km_dmt_product,
        kcat_leak=params.kcat_dmt_leak,
        km_leak=params.km_dmt_leak,
    )

    v_oc = phi * v_oc_in + (1.0 - phi) * v_oc_out
    v_product = phi * v_product_in + (1.0 - phi) * v_product_out
    v_leak = phi * v_leak_in + (1.0 - phi) * v_leak_out
    return v_oc, v_product, v_leak


def glabridin_rates(
    state: np.ndarray, params: GlabridinKineticParameters, *, pt_gate_level: float, oc_gate_level: float, dmt_gate_level: float
) -> tuple[float, float, float, float]:
    """Return cell-average PT, OC, DMT(9), DMT(11) rates with shared DMT pool."""
    x9, x10, x11, _x13, _x15 = np.maximum(state, 0.0)
    phi = params.phi
    pt = (phase_concentrations(params.pt_total * pt_gate_level, params.partition_pt, phi),
          phase_concentrations(params.oc_total * oc_gate_level, params.partition_oc, phi),
          phase_concentrations(params.dmt_total * dmt_gate_level, params.partition_dmt, phi))
    p9 = phase_concentrations(x9, params.partition_9, phi)
    p10 = phase_concentrations(x10, params.partition_10, phi)
    p11 = phase_concentrations(x11, params.partition_11, phi)
    pt_dense = _mm_rate(pt[0][0], p9[0], params.kcat_pt * params.activity_dense_pt, params.km_pt)
    pt_dilute = _mm_rate(pt[0][1], p9[1], params.kcat_pt * params.activity_dilute_pt, params.km_pt)
    oc_dense = _mm_rate(pt[1][0], p10[0], params.kcat_oc * params.activity_dense_oc, params.km_oc)
    oc_dilute = _mm_rate(pt[1][1], p10[1], params.kcat_oc * params.activity_dilute_oc, params.km_oc)
    d15_dense, d13_dense = competitive_dmt_rates(dmt=pt[2][0], substrate_a=p9[0], intermediate_b=p11[0], kcat_product=params.kcat_dmt_11 * params.activity_dense_dmt, km_product=params.km_dmt_11, kcat_leak=params.kcat_dmt_9 * params.activity_dense_dmt, km_leak=params.km_dmt_9)
    d15_dilute, d13_dilute = competitive_dmt_rates(dmt=pt[2][1], substrate_a=p9[1], intermediate_b=p11[1], kcat_product=params.kcat_dmt_11 * params.activity_dilute_dmt, km_product=params.km_dmt_11, kcat_leak=params.kcat_dmt_9 * params.activity_dilute_dmt, km_leak=params.km_dmt_9)
    average = lambda dense, dilute: phi * dense + (1 - phi) * dilute
    return average(pt_dense, pt_dilute), average(oc_dense, oc_dilute), average(d13_dense, d13_dilute), average(d15_dense, d15_dilute)


def simulate_glabridin(
    params: GlabridinKineticParameters, *, pt_gate: InductionGate = InductionGate(on_time=0.0, basal=0.0, induced=1.0),
    oc_gate: InductionGate = InductionGate(on_time=0.0, basal=0.0, induced=1.0),
    dmt_gate: InductionGate = InductionGate(on_time=0.0, basal=0.0, induced=1.0), initial: tuple[float, float, float, float, float] = (10.0, 0.0, 0.0, 0.0, 0.0),
    t_end: float = 24.0, points: int = 241,
) -> GlabridinSimulationResult:
    """Segmented two-compartment ODE; no degradation gives pathway mass balance."""
    from scipy.integrate import solve_ivp, trapezoid
    params.validate(); pt_gate.validate(); oc_gate.validate(); dmt_gate.validate()
    if t_end <= 0 or points < 2 or any(value < 0 for value in initial):
        raise ValueError("invalid simulation horizon, point count, or initial state")
    evaluation = np.linspace(0.0, t_end, points)
    state = np.asarray(initial, dtype=float); all_t: list[np.ndarray] = []; all_y: list[np.ndarray] = []
    for start, end in zip(_piecewise_boundaries(t_end, pt_gate, oc_gate, dmt_gate)[:-1], _piecewise_boundaries(t_end, pt_gate, oc_gate, dmt_gate)[1:]):
        segment = evaluation[(evaluation >= start) & (evaluation <= end)]
        segment = np.unique(np.concatenate(([start, end], segment if segment.size else np.asarray([]))))
        def rhs(time: float, current: np.ndarray) -> np.ndarray:
            vpt, voc, v13, v15 = glabridin_rates(current, params, pt_gate_level=gate_value(time, pt_gate), oc_gate_level=gate_value(time, oc_gate), dmt_gate_level=gate_value(time, dmt_gate))
            x9, x10, x11, x13, x15 = np.maximum(current, 0.0)
            return np.array([-vpt-v13-params.kdeg_9*x9, vpt-voc-params.kdeg_10*x10, voc-v15-params.kdeg_11*x11, v13-params.kdeg_13*x13, v15-params.kdeg_15*x15])
        solved = solve_ivp(rhs, (start, end), state, t_eval=segment, method="LSODA", rtol=1e-8, atol=1e-10)
        if not solved.success: raise RuntimeError(solved.message)
        times, values = solved.t, np.maximum(solved.y, 0.0)
        if all_t: times, values = times[1:], values[:, 1:]
        all_t.append(times); all_y.append(values); state = values[:, -1]
    time = np.concatenate(all_t); concentrations = np.concatenate(all_y, axis=1); order = np.argsort(time)
    time, concentrations = time[order], concentrations[:, order]
    degradation_rate = params.kdeg_9 * concentrations[0] + params.kdeg_10 * concentrations[1] + params.kdeg_11 * concentrations[2] + params.kdeg_13 * concentrations[3] + params.kdeg_15 * concentrations[4]
    degradation_loss = float(trapezoid(degradation_rate, time))
    return GlabridinSimulationResult(time, concentrations, np.asarray([gate_value(float(t), pt_gate) for t in time]), np.asarray([gate_value(float(t), oc_gate) for t in time]), np.asarray([gate_value(float(t), dmt_gate) for t in time]), degradation_loss)


def simulate_cascade(
    params: CascadeParameters,
    initial: tuple[float, float, float] = (10.0, 0.0, 0.0),
    t_end: float = 24.0,
    points: int = 241,
) -> SimulationResult:
    from scipy.integrate import solve_ivp
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


def simulate_piecewise_induction(
    params: CompetitiveCascadeParameters,
    *,
    oc_gate: InductionGate = InductionGate(on_time=0.0, basal=0.0, induced=1.0),
    dmt_gate: InductionGate = InductionGate(on_time=4.0, basal=0.0, induced=1.0),
    initial: tuple[float, float, float, float] = (10.0, 0.0, 0.0, 0.0),
    t_end: float = 24.0,
    points: int = 241,
) -> CompetitiveSimulationResult:
    """Simulate OC-first/DMT-later cascade with shared DMT competition.

    Step gates are integrated piecewise at on/off boundaries. Sigmoid gates are
    continuous and can be handled in a single solver pass.
    """
    from scipy.integrate import solve_ivp
    params.validate()
    oc_gate.validate()
    dmt_gate.validate()
    if t_end <= 0 or points < 2:
        raise ValueError("t_end must be positive and points must be at least 2")
    if any(value < 0 for value in initial):
        raise ValueError("initial concentrations must be nonnegative")

    evaluation_times = np.linspace(0.0, t_end, points)
    boundaries = _piecewise_boundaries(t_end, oc_gate, dmt_gate)

    all_t: list[np.ndarray] = []
    all_y: list[np.ndarray] = []
    state = np.asarray(initial, dtype=float)

    for start, end in zip(boundaries[:-1], boundaries[1:]):
        mask = (evaluation_times >= start) & (evaluation_times <= end)
        segment_eval = evaluation_times[mask]
        if segment_eval.size == 0:
            segment_eval = np.asarray([start, end])
        segment_eval = np.unique(np.concatenate(([start, end], segment_eval)))

        def rhs(time: float, current: np.ndarray) -> np.ndarray:
            oc_level = gate_value(time, oc_gate)
            dmt_level = gate_value(time, dmt_gate)
            v_oc, v_product, v_leak = competitive_cascade_rates(
                current,
                params,
                oc_gate_level=oc_level,
                dmt_gate_level=dmt_level,
            )
            a, b, product, byproduct = np.maximum(current, 0.0)
            return np.array(
                [
                    -v_oc - v_leak - params.kdeg_a * a,
                    v_oc - v_product - params.kdeg_b * b,
                    v_product - params.kdeg_product * product,
                    v_leak - params.kdeg_byproduct * byproduct,
                ]
            )

        solution = solve_ivp(
            rhs,
            (start, end),
            state,
            t_eval=segment_eval,
            method="LSODA",
            rtol=1e-8,
            atol=1e-10,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        segment_t = solution.t
        segment_y = np.maximum(solution.y, 0.0)
        if all_t:
            segment_t = segment_t[1:]
            segment_y = segment_y[:, 1:]
        all_t.append(segment_t)
        all_y.append(segment_y)
        state = segment_y[:, -1]

    time = np.concatenate(all_t)
    concentrations = np.concatenate(all_y, axis=1)
    order = np.argsort(time)
    time = time[order]
    concentrations = concentrations[:, order]
    oc_values = np.asarray([gate_value(float(t), oc_gate) for t in time], dtype=float)
    dmt_values = np.asarray([gate_value(float(t), dmt_gate) for t in time], dtype=float)
    return CompetitiveSimulationResult(time, concentrations, oc_values, dmt_values)


def _piecewise_boundaries(t_end: float, *gates: InductionGate) -> list[float]:
    boundaries = {0.0, float(t_end)}
    for gate in gates:
        if gate.mode != "step":
            continue
        for boundary in (gate.on_time, gate.off_time):
            if boundary is not None and 0.0 < boundary < t_end:
                boundaries.add(float(boundary))
    return sorted(boundaries)
