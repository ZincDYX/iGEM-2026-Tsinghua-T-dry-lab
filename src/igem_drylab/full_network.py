"""Auditable Galatea M3/M4 full-network model.

This module is deliberately separate from the legacy reduced M4 kernel.  It
models compounds 8--15, the ten documented reactions, explicit two-phase
partitioning, and one competing enzyme pool per enzyme in each phase.  It is a
mechanistic sensitivity model; it does not infer any kinetic input from M1/M2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from scipy.integrate import solve_ivp

COMPOUNDS = ("8", "9", "10", "11", "12", "13", "14", "15")
REACTIONS = (
    ("R1", "PTR", "8", "9"), ("R2", "PT", "9", "10"), ("R3", "OC", "10", "11"),
    ("R4", "DMT", "8", "12"), ("R5", "DMT", "9", "13"), ("R6", "DMT", "10", "14"),
    ("R7", "DMT", "11", "15"), ("R8", "PTR", "12", "13"), ("R9", "PT", "13", "14"),
    ("R10", "OC", "14", "15"),
)
ENZYME_SUBSTRATES = {"PTR": ("8", "12"), "PT": ("9", "13"), "OC": ("10", "14"), "DMT": ("8", "9", "10", "11")}
_INDEX = {compound: index for index, compound in enumerate(COMPOUNDS)}


@dataclass(frozen=True)
class PhaseDistribution:
    """Mass-conserving concentrations for one enzyme or metabolite."""

    dense: float
    dilute: float

    def cell_average(self, phi: float) -> float:
        return phi * self.dense + (1.0 - phi) * self.dilute


@dataclass(frozen=True)
class EffectiveRecruitment:
    oc_bound: float
    dmt_bound: float
    oc: PhaseDistribution
    dmt: PhaseDistribution
    target_ratio: float


def phase_partition(average: float, kp: float, phi: float) -> PhaseDistribution:
    """Partition a cell-average concentration without changing total mass."""
    if average < 0 or kp <= 0 or not 0 <= phi <= 1:
        raise ValueError("invalid_average_kp_or_phi")
    if phi == 0:
        return PhaseDistribution(dense=0.0, dilute=average)
    if phi == 1:
        return PhaseDistribution(dense=average, dilute=0.0)
    dilute = average / ((1.0 - phi) + phi * kp)
    return PhaseDistribution(dense=kp * dilute, dilute=dilute)


def effective_ratio_recruitment(
    *, oc_total: float, dmt_total: float, phi: float, slot_ratio_sh3_to_pdz: float,
    total_recruited_fraction: float, recruitment_bias_oc_vs_dmt: float = 1.0,
) -> EffectiveRecruitment:
    """Allocate a finite recruited pool in a requested OC:DMT ratio.

    ``slot_ratio_sh3_to_pdz`` is an engineering capacity ratio, not a measured
    binding affinity.  Caps are resolved deterministically and all enzyme mass
    remains in either the dense or dilute phase.
    """
    values = (oc_total, dmt_total, slot_ratio_sh3_to_pdz, total_recruited_fraction, recruitment_bias_oc_vs_dmt)
    if any(value < 0 for value in values) or not 0 <= phi < 1:
        raise ValueError("invalid_effective_ratio_recruitment_input")
    if total_recruited_fraction > 1:
        raise ValueError("total_recruited_fraction_must_not_exceed_one")
    if phi == 0:
        return EffectiveRecruitment(0.0, 0.0, PhaseDistribution(0.0, oc_total), PhaseDistribution(0.0, dmt_total), 0.0)
    target_ratio = slot_ratio_sh3_to_pdz * recruitment_bias_oc_vs_dmt
    capacity = total_recruited_fraction * (oc_total + dmt_total)
    if target_ratio == 0:
        oc_bound, dmt_bound = 0.0, min(capacity, dmt_total)
    else:
        oc_bound = min(oc_total, capacity * target_ratio / (target_ratio + 1.0))
        dmt_bound = min(dmt_total, capacity - oc_bound)
        # If a cap leaves capacity unused, the other enzyme receives it first.
        remaining = capacity - oc_bound - dmt_bound
        if remaining > 0:
            add_oc = min(remaining, oc_total - oc_bound)
            oc_bound += add_oc
            dmt_bound += min(remaining - add_oc, dmt_total - dmt_bound)
    oc = PhaseDistribution(oc_bound / phi, (oc_total - oc_bound) / (1.0 - phi) if phi < 1 else 0.0)
    dmt = PhaseDistribution(dmt_bound / phi, (dmt_total - dmt_bound) / (1.0 - phi) if phi < 1 else 0.0)
    return EffectiveRecruitment(oc_bound, dmt_bound, oc, dmt, target_ratio)


@dataclass(frozen=True)
class ReactionKinetics:
    reaction_id: str
    enzyme: Literal["PTR", "PT", "OC", "DMT"]
    substrate: str
    product: str
    kcat: float
    km: float

    def validate(self) -> None:
        if self.reaction_id not in {item[0] for item in REACTIONS} or self.substrate not in _INDEX or self.product not in _INDEX:
            raise ValueError("invalid_reaction_identity")
        if self.kcat < 0 or self.km <= 0:
            raise ValueError("kcat_must_be_nonnegative_and_km_positive")


@dataclass(frozen=True)
class TransportParameters:
    enabled: bool = False
    access: Literal["dilute_phase", "cell_average"] = "dilute_phase"
    rate: float = 0.0
    outside_over_inside: dict[str, float] = field(default_factory=lambda: {compound: 0.0 for compound in COMPOUNDS})

    def validate(self) -> None:
        if self.rate < 0 or set(self.outside_over_inside) != set(COMPOUNDS) or any(value < 0 for value in self.outside_over_inside.values()):
            raise ValueError("invalid_transport_parameters")


@dataclass(frozen=True)
class TemporalGate:
    """Constitutive by default; delayed ramp is an explicit ablation only."""

    mode: Literal["constitutive", "published_delayed_ramp"] = "constitutive"
    disable_time: float = 0.0
    ramp_ceiling: float = 0.8
    ramp_slope: float = 0.8

    def validate(self) -> None:
        if self.mode not in {"constitutive", "published_delayed_ramp"}:
            raise ValueError("invalid_temporal_gate_mode")
        if not all(np.isfinite(value) and value >= 0 for value in (self.disable_time, self.ramp_ceiling, self.ramp_slope)):
            raise ValueError("temporal_gate_parameters_must_be_finite_and_nonnegative")

    def value(self, time: float) -> float:
        if self.mode == "constitutive":
            return 1.0
        if time <= self.disable_time:
            return 0.0
        return min(self.ramp_ceiling, (time - self.disable_time) * self.ramp_slope)


@dataclass(frozen=True)
class FullNetworkParameters:
    phi: float
    enzyme_distributions: dict[str, PhaseDistribution]
    metabolite_kp: dict[str, float]
    reactions: tuple[ReactionKinetics, ...]
    activity_dense: dict[str, float] = field(default_factory=lambda: {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES})
    activity_dilute: dict[str, float] = field(default_factory=lambda: {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES})
    transport: TransportParameters = field(default_factory=TransportParameters)
    dmt_gate: TemporalGate = field(default_factory=TemporalGate)
    scenario: Literal["homogeneous_constitutive", "homogeneous_published_like_temporal", "galatea_spatial", "galatea_spatiotemporal_ablation"] = "galatea_spatial"
    unit_mode: Literal["physical", "author_native_sensitivity"] = "physical"

    def validate(self) -> None:
        if not 0 <= self.phi < 1:
            raise ValueError("phi_must_be_between_zero_and_one_exclusive")
        if set(self.enzyme_distributions) != set(ENZYME_SUBSTRATES) or set(self.metabolite_kp) != set(COMPOUNDS):
            raise ValueError("complete_enzyme_and_metabolite_parameterization_required")
        canonical = tuple((item.reaction_id, item.enzyme, item.substrate, item.product) for item in self.reactions)
        if canonical != REACTIONS:
            raise ValueError("full_ten_reaction_network_required")
        if any(value <= 0 or not np.isfinite(value) for value in self.metabolite_kp.values()):
            raise ValueError("metabolite_partition_coefficients_must_be_positive_and_finite")
        for distribution in self.enzyme_distributions.values():
            if any(value < 0 or not np.isfinite(value) for value in (distribution.dense, distribution.dilute)):
                raise ValueError("enzyme_phase_concentrations_must_be_nonnegative_and_finite")
        if set(self.activity_dense) != set(ENZYME_SUBSTRATES) or set(self.activity_dilute) != set(ENZYME_SUBSTRATES):
            raise ValueError("activity_dictionaries_must_cover_exactly_all_enzymes")
        if any(value < 0 or not np.isfinite(value) for value in [*self.activity_dense.values(), *self.activity_dilute.values()]):
            raise ValueError("activity_multipliers_must_be_nonnegative_and_finite")
        if self.scenario == "galatea_spatial" and self.dmt_gate.mode != "constitutive":
            raise ValueError("galatea_spatial_requires_constitutive_dmt_unless_using_ablation")
        if self.scenario == "homogeneous_constitutive" and (self.phi != 0 or self.dmt_gate.mode != "constitutive"):
            raise ValueError("homogeneous_constitutive_requires_phi_zero_and_constitutive_dmt")
        if self.scenario == "homogeneous_published_like_temporal" and (self.phi != 0 or self.dmt_gate.mode != "published_delayed_ramp"):
            raise ValueError("homogeneous_published_like_temporal_requires_phi_zero_and_delayed_dmt")
        self.dmt_gate.validate()
        self.transport.validate()
        for reaction in self.reactions:
            reaction.validate()


@dataclass(frozen=True)
class FullNetworkResult:
    time: np.ndarray
    intracellular: np.ndarray  # cell-average, 8 x time
    extracellular: np.ndarray  # 8 x time
    fluxes: np.ndarray  # 10 x time; cell-average fluxes
    flux_integrals: dict[str, float]
    diagnostics: dict[str, float]
    unit_mode: Literal["physical", "author_native_sensitivity"]


def _phase_rates(phase_substrates: dict[str, float], enzymes: dict[str, float], reactions: tuple[ReactionKinetics, ...], activities: dict[str, float], dmt_gate: float) -> dict[str, float]:
    rates: dict[str, float] = {}
    by_enzyme: dict[str, list[ReactionKinetics]] = {enzyme: [] for enzyme in ENZYME_SUBSTRATES}
    for reaction in reactions:
        by_enzyme[reaction.enzyme].append(reaction)
    for enzyme, entries in by_enzyme.items():
        enzyme_amount = enzymes[enzyme] * activities[enzyme] * (dmt_gate if enzyme == "DMT" else 1.0)
        denominator = 1.0 + sum(max(phase_substrates[item.substrate], 0.0) / item.km for item in entries)
        for item in entries:
            numerator = max(phase_substrates[item.substrate], 0.0) / item.km
            rates[item.reaction_id] = enzyme_amount * item.kcat * numerator / denominator if enzyme_amount > 0 else 0.0
    return rates


def _transport_flux(intracellular: np.ndarray, extracellular: np.ndarray, params: FullNetworkParameters) -> np.ndarray:
    if not params.transport.enabled or params.transport.rate == 0:
        return np.zeros(8)
    access = np.asarray([
        phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dilute
        if params.transport.access == "dilute_phase" else float(intracellular[index])
        for index, compound in enumerate(COMPOUNDS)
    ])
    equilibrium = np.asarray([params.transport.outside_over_inside[compound] for compound in COMPOUNDS])
    forward = equilibrium * params.transport.rate / (equilibrium + 1.0)
    reverse = params.transport.rate / (equilibrium + 1.0)
    return forward * access - reverse * extracellular


def simulate_full_network(params: FullNetworkParameters, *, initial_intracellular: dict[str, float], initial_extracellular: dict[str, float] | None = None, t_end: float, points: int = 501) -> FullNetworkResult:
    """Run the full ten-reaction Galatea two-phase model with LSODA."""
    params.validate()
    if t_end <= 0 or points < 2 or set(initial_intracellular) != set(COMPOUNDS):
        raise ValueError("complete_nonnegative_initial_state_and_horizon_required")
    initial_extracellular = initial_extracellular or {compound: 0.0 for compound in COMPOUNDS}
    if set(initial_extracellular) != set(COMPOUNDS) or any(value < 0 for value in [*initial_intracellular.values(), *initial_extracellular.values()]):
        raise ValueError("initial_states_must_be_complete_and_nonnegative")
    initial = np.asarray([*(initial_intracellular[compound] for compound in COMPOUNDS), *(initial_extracellular[compound] for compound in COMPOUNDS)], dtype=float)

    def rhs(time: float, state: np.ndarray) -> np.ndarray:
        intracellular = np.maximum(state[:8], 0.0)
        extracellular = np.maximum(state[8:], 0.0)
        dense = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dense for index, compound in enumerate(COMPOUNDS)}
        dilute = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dilute for index, compound in enumerate(COMPOUNDS)}
        dense_enzymes = {enzyme: item.dense for enzyme, item in params.enzyme_distributions.items()}
        dilute_enzymes = {enzyme: item.dilute for enzyme, item in params.enzyme_distributions.items()}
        gate = params.dmt_gate.value(time)
        dense_rates = _phase_rates(dense, dense_enzymes, params.reactions, params.activity_dense, gate)
        dilute_rates = _phase_rates(dilute, dilute_enzymes, params.reactions, params.activity_dilute, gate)
        rates = {reaction_id: params.phi * dense_rates[reaction_id] + (1.0 - params.phi) * dilute_rates[reaction_id] for reaction_id, *_ in REACTIONS}
        derivative = np.zeros(8)
        for reaction_id, _enzyme, substrate, product in REACTIONS:
            flux = rates[reaction_id]
            derivative[_INDEX[substrate]] -= flux
            derivative[_INDEX[product]] += flux
        transport = _transport_flux(intracellular, extracellular, params)
        return np.concatenate((derivative - transport, transport))

    evaluation = np.linspace(0.0, t_end, points)
    solved = solve_ivp(rhs, (0.0, t_end), initial, t_eval=evaluation, method="LSODA", rtol=1e-8, atol=1e-10)
    if not solved.success:
        raise RuntimeError(solved.message)
    raw_states = solved.y
    negative_tolerance = -1e-9
    if float(raw_states.min()) < negative_tolerance:
        raise RuntimeError(f"numerical_negative_concentration_exceeds_tolerance:{raw_states.min():.3e}")
    states = np.where(raw_states < 0.0, 0.0, raw_states)
    fluxes = np.empty((10, solved.t.size))
    for column, (time, state) in enumerate(zip(solved.t, states.T, strict=True)):
        intracellular = state[:8]
        dense = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dense for index, compound in enumerate(COMPOUNDS)}
        dilute = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dilute for index, compound in enumerate(COMPOUNDS)}
        dense_rates = _phase_rates(dense, {enzyme: item.dense for enzyme, item in params.enzyme_distributions.items()}, params.reactions, params.activity_dense, params.dmt_gate.value(float(time)))
        dilute_rates = _phase_rates(dilute, {enzyme: item.dilute for enzyme, item in params.enzyme_distributions.items()}, params.reactions, params.activity_dilute, params.dmt_gate.value(float(time)))
        fluxes[:, column] = [params.phi * dense_rates[reaction_id] + (1 - params.phi) * dilute_rates[reaction_id] for reaction_id, *_ in REACTIONS]
    integrals = {reaction_id: float(np.trapezoid(fluxes[index], solved.t)) for index, (reaction_id, *_rest) in enumerate(REACTIONS)}
    initial_8 = initial_intracellular["8"]
    final_intracellular, final_extracellular = states[:8, -1], states[8:, -1]
    final_15_total = float(final_intracellular[_INDEX["15"]] + final_extracellular[_INDEX["15"]])
    final_13_total = float(final_intracellular[_INDEX["13"]] + final_extracellular[_INDEX["13"]])
    dmt_total = sum(integrals[f"R{index}"] for index in (4, 5, 6, 7))
    eps = 1e-12
    diagnostics = {
        "final_15_total": final_15_total,
        "final_13_total": final_13_total,
        "final_13_extracellular": float(final_extracellular[_INDEX["13"]]),
        "target_yield_fraction": final_15_total / (initial_8 + eps),
        "branch_9_to_13_fraction": integrals["R5"] / (integrals["R2"] + integrals["R5"] + eps),
        "dmt_late_selectivity": integrals["R7"] / (dmt_total + eps),
        "early_dmt_fraction": 1.0 - integrals["R7"] / (dmt_total + eps),
        "oc_before_dmt_route_fraction": integrals["R7"] / (integrals["R7"] + integrals["R10"] + eps),
        "mass_balance_error": abs(float(states[:, 0].sum() - states[:, -1].sum())),
    }
    return FullNetworkResult(solved.t, states[:8], states[8:], fluxes, integrals, diagnostics, params.unit_mode)
