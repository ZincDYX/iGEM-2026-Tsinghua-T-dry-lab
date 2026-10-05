"""Auditable Galatea M3/M4 full-network model.

This module is deliberately separate from the legacy reduced M4 kernel.  It
models compounds 8--15, the ten documented reactions, explicit two-phase
partitioning, and one competing enzyme pool per enzyme in each phase.  It is a
mechanistic sensitivity model; it does not infer any kinetic input from M1/M2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from types import SimpleNamespace

import numpy as np
from scipy.integrate import solve_ivp
from .kinetics import InductionGate, gate_value

COMPOUNDS = ("8", "9", "10", "11", "12", "13", "14", "15")
REACTIONS = (
    ("R1", "PTR", "8", "9"), ("R2", "PT", "9", "10"), ("R3", "OC", "10", "11"),
    ("R4", "DMT", "8", "12"), ("R5", "DMT", "9", "13"), ("R6", "DMT", "10", "14"),
    ("R7", "DMT", "11", "15"), ("R8", "PTR", "12", "13"), ("R9", "PT", "13", "14"),
    ("R10", "OC", "14", "15"),
)
ENZYME_SUBSTRATES = {"PTR": ("8", "12"), "PT": ("9", "13"), "OC": ("10", "14"), "DMT": ("8", "9", "10", "11")}
_INDEX = {compound: index for index, compound in enumerate(COMPOUNDS)}
NUMERICAL_NEGATIVE_TOLERANCE = -1e-8
FULL_NETWORK_FORMULA_VERSION = "galatea-dynamic-volume-v2-2026-10-04"
ACTIVE_NETWORK_FORMULA_VERSION = "galatea-oc-dmt-verified-absence-v1-2026-10-05"


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
    if not all(np.isfinite(value) for value in (average, kp, phi)) or average < 0 or kp <= 0 or not 0 <= phi <= 1:
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
    if any(not np.isfinite(value) or value < 0 for value in values) or not 0 <= phi < 1:
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
        if not np.isfinite(self.kcat) or not np.isfinite(self.km) or self.kcat < 0 or self.km <= 0:
            raise ValueError("kcat_must_be_nonnegative_and_km_positive")


@dataclass(frozen=True)
class TransportParameters:
    enabled: bool = False
    access: Literal["dilute_phase", "cell_average"] = "dilute_phase"
    rate: float = 0.0
    outside_over_inside: dict[str, float] = field(default_factory=lambda: {compound: 0.0 for compound in COMPOUNDS})
    intracellular_volume_l: float | None = None
    extracellular_volume_l: float | None = None

    def validate(self) -> None:
        if not np.isfinite(self.rate) or self.rate < 0 or set(self.outside_over_inside) != set(COMPOUNDS) or any(not np.isfinite(value) or value < 0 for value in self.outside_over_inside.values()):
            raise ValueError("invalid_transport_parameters")
        if self.access not in {"dilute_phase", "cell_average"}:
            raise ValueError("invalid_transport_access")
        volumes = (self.intracellular_volume_l, self.extracellular_volume_l)
        if any(value is not None for value in volumes) or self.enabled:
            if any(value is None or not np.isfinite(value) or value <= 0 for value in volumes):
                raise ValueError("transport_requires_explicit_positive_compartment_volumes_l")

    @property
    def extracellular_to_intracellular_volume_ratio(self) -> float:
        if self.intracellular_volume_l is None:
            return 1.0  # only used when extracellular states are identically zero
        return self.extracellular_volume_l / self.intracellular_volume_l


@dataclass(frozen=True)
class TemporalGate:
    """Constitutive by default; delayed ramp is an explicit ablation only."""

    mode: Literal["constitutive", "published_delayed_ramp", "configured_induction"] = "constitutive"
    disable_time: float = 0.0
    ramp_ceiling: float = 0.8
    ramp_slope: float = 0.8
    induction: InductionGate | None = None

    def validate(self) -> None:
        if self.mode not in {"constitutive", "published_delayed_ramp", "configured_induction"}:
            raise ValueError("invalid_temporal_gate_mode")
        if self.mode == "configured_induction":
            if self.induction is None:
                raise ValueError("configured_induction_requires_all_gate_fields")
            self.induction.validate()
        if not all(np.isfinite(value) and value >= 0 for value in (self.disable_time, self.ramp_ceiling, self.ramp_slope)):
            raise ValueError("temporal_gate_parameters_must_be_finite_and_nonnegative")

    def value(self, time: float) -> float:
        if self.mode == "configured_induction":
            return gate_value(time, self.induction)
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
    pt_gate: TemporalGate = field(default_factory=TemporalGate)
    oc_gate: TemporalGate = field(default_factory=TemporalGate)
    scenario: Literal["homogeneous_constitutive", "homogeneous_published_like_temporal", "galatea_spatial", "galatea_spatiotemporal_ablation"] = "galatea_spatial"
    unit_mode: Literal["physical", "author_native_sensitivity"] = "physical"
    network_variant: Literal["full_ten", "oc_dmt_verified_absence"] = "full_ten"
    absence_evidence: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not 0 <= self.phi < 1:
            raise ValueError("phi_must_be_between_zero_and_one_exclusive")
        active = self.network_variant == "oc_dmt_verified_absence"
        if self.network_variant not in {"full_ten","oc_dmt_verified_absence"}:
            raise ValueError("unknown_active_network_variant")
        expected_enzymes = {"OC","DMT"} if active else set(ENZYME_SUBSTRATES)
        if active and (self.unit_mode != "physical" or self.absence_evidence.get("confirmed_absent_enzymes") !=
                      {"PTR":"genetic_and_background_activity_absent","PT":"genetic_and_background_activity_absent"} or
                      not all(self.absence_evidence.get(k) for k in ("construct_id","condition_id","host","strain","source_reference","verification_method","reviewed_by","artifact_sha256"))):
            raise ValueError("active_network_requires_bound_verified_absence_evidence_and_physical_units")
        if set(self.enzyme_distributions) != expected_enzymes or set(self.metabolite_kp) != set(COMPOUNDS):
            raise ValueError("complete_enzyme_and_metabolite_parameterization_required")
        canonical = tuple((item.reaction_id, item.enzyme, item.substrate, item.product) for item in self.reactions)
        expected_reactions = tuple(r for r in REACTIONS if r[1] in expected_enzymes)
        if canonical != expected_reactions:
            raise ValueError("full_ten_reaction_network_required")
        if any(value <= 0 or not np.isfinite(value) for value in self.metabolite_kp.values()):
            raise ValueError("metabolite_partition_coefficients_must_be_positive_and_finite")
        for distribution in self.enzyme_distributions.values():
            if any(value < 0 or not np.isfinite(value) for value in (distribution.dense, distribution.dilute)):
                raise ValueError("enzyme_phase_concentrations_must_be_nonnegative_and_finite")
        if set(self.activity_dense) != expected_enzymes or set(self.activity_dilute) != expected_enzymes:
            raise ValueError("activity_dictionaries_must_cover_exactly_all_enzymes")
        if any(value < 0 or not np.isfinite(value) for value in [*self.activity_dense.values(), *self.activity_dilute.values()]):
            raise ValueError("activity_multipliers_must_be_nonnegative_and_finite")
        if self.scenario == "galatea_spatial" and self.dmt_gate.mode != "constitutive":
            raise ValueError("galatea_spatial_requires_constitutive_dmt_unless_using_ablation")
        if self.scenario == "homogeneous_constitutive" and (self.phi != 0 or any(gate.mode != "constitutive" for gate in (self.pt_gate, self.oc_gate, self.dmt_gate))):
            raise ValueError("homogeneous_constitutive_requires_phi_zero_and_constitutive_dmt")
        if self.scenario == "homogeneous_published_like_temporal" and (self.phi != 0 or self.dmt_gate.mode == "constitutive"):
            raise ValueError("homogeneous_published_like_temporal_requires_phi_zero_and_delayed_dmt")
        self.dmt_gate.validate()
        self.pt_gate.validate()
        self.oc_gate.validate()
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
    diagnostics: dict[str, float | None]
    unit_mode: Literal["physical", "author_native_sensitivity"]
    raw_intracellular: np.ndarray | None = None
    raw_extracellular: np.ndarray | None = None
    transport_integrals: dict[str, dict[str, float]] = field(default_factory=dict)
    solver_settings: dict = field(default_factory=dict)


def phase_competitive_rates(phase_substrates: dict[str, float], enzymes: dict[str, float], reactions: tuple[ReactionKinetics, ...], activities: dict[str, float], dmt_gate: float) -> dict[str, float]:
    rates: dict[str, float] = {}
    by_enzyme: dict[str, list[ReactionKinetics]] = {enzyme: [] for enzyme in ENZYME_SUBSTRATES}
    for reaction in reactions:
        by_enzyme[reaction.enzyme].append(reaction)
    for enzyme, entries in by_enzyme.items():
        if not entries:
            continue
        enzyme_amount = enzymes[enzyme] * activities[enzyme] * (dmt_gate if enzyme == "DMT" else 1.0)
        denominator = 1.0 + sum(max(phase_substrates[item.substrate], 0.0) / item.km for item in entries)
        for item in entries:
            numerator = max(phase_substrates[item.substrate], 0.0) / item.km
            rates[item.reaction_id] = enzyme_amount * item.kcat * numerator / denominator if enzyme_amount > 0 else 0.0
    return rates


def _transport_rates(intracellular: np.ndarray, extracellular: np.ndarray, params: FullNetworkParameters) -> tuple[np.ndarray, np.ndarray]:
    if not params.transport.enabled or params.transport.rate == 0:
        return np.zeros(8), np.zeros(8)
    access = np.asarray([
        phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dilute
        if params.transport.access == "dilute_phase" else float(intracellular[index])
        for index, compound in enumerate(COMPOUNDS)
    ])
    equilibrium = np.asarray([params.transport.outside_over_inside[compound] for compound in COMPOUNDS])
    forward = equilibrium * params.transport.rate / (equilibrium + 1.0)
    reverse = params.transport.rate / (equilibrium + 1.0)
    return forward * access, reverse * extracellular


def simulate_full_network(params: FullNetworkParameters, *, initial_intracellular: dict[str, float], initial_extracellular: dict[str, float] | None = None, t_end: float, points: int = 501, method: Literal["LSODA", "BDF", "Radau"] = "LSODA", rtol: float = 1e-8, atol: float = 1e-12) -> FullNetworkResult:
    """Run the full ten-reaction Galatea two-phase model with LSODA."""
    params.validate()
    if method not in {"LSODA", "BDF", "Radau"} or not all(np.isfinite(v) and v > 0 for v in (rtol, atol)):
        raise ValueError("unsupported_or_invalid_production_solver_settings")
    if not np.isfinite(t_end) or t_end <= 0 or points < 2 or set(initial_intracellular) != set(COMPOUNDS):
        raise ValueError("complete_nonnegative_initial_state_and_horizon_required")
    initial_extracellular = initial_extracellular or {compound: 0.0 for compound in COMPOUNDS}
    if set(initial_extracellular) != set(COMPOUNDS) or any(not np.isfinite(value) or value < 0 for value in [*initial_intracellular.values(), *initial_extracellular.values()]):
        raise ValueError("initial_states_must_be_complete_and_nonnegative")
    if any(initial_extracellular.values()) and params.transport.intracellular_volume_l is None:
        raise ValueError("extracellular_initial_concentrations_require_compartment_volumes")
    volume_ratio = params.transport.extracellular_to_intracellular_volume_ratio
    initial = np.asarray([*(initial_intracellular[compound] for compound in COMPOUNDS), *(initial_extracellular[compound] for compound in COMPOUNDS), *([0.0] * 26)], dtype=float)

    def instantaneous(time: float, state: np.ndarray):
        intracellular = np.maximum(state[:8], 0.0)
        extracellular = np.maximum(state[8:16], 0.0)
        dense = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dense for index, compound in enumerate(COMPOUNDS)}
        dilute = {compound: phase_partition(float(intracellular[index]), params.metabolite_kp[compound], params.phi).dilute for index, compound in enumerate(COMPOUNDS)}
        gates = {"PT": params.pt_gate.value(time), "OC": params.oc_gate.value(time)}
        dense_enzymes = {enzyme: item.dense * gates.get(enzyme, 1.0) for enzyme, item in params.enzyme_distributions.items()}
        dilute_enzymes = {enzyme: item.dilute * gates.get(enzyme, 1.0) for enzyme, item in params.enzyme_distributions.items()}
        gate = params.dmt_gate.value(time)
        dense_rates = phase_competitive_rates(dense, dense_enzymes, params.reactions, params.activity_dense, gate)
        dilute_rates = phase_competitive_rates(dilute, dilute_enzymes, params.reactions, params.activity_dilute, gate)
        rates = {reaction_id: params.phi * dense_rates.get(reaction_id,0.) + (1.0 - params.phi) * dilute_rates.get(reaction_id,0.) for reaction_id, *_ in REACTIONS}
        forward, reverse = _transport_rates(intracellular, extracellular, params)
        return rates, forward, reverse

    def rhs(time: float, state: np.ndarray) -> np.ndarray:
        rates, forward, reverse = instantaneous(time, state)
        derivative = np.zeros(8)
        for reaction_id, _enzyme, substrate, product in REACTIONS:
            flux = rates[reaction_id]
            derivative[_INDEX[substrate]] -= flux
            derivative[_INDEX[product]] += flux
        transport = forward - reverse
        # J is normalized by intracellular volume; both states are their own
        # compartment concentrations. Vi*dCi + Ve*dCe therefore conserves amount.
        return np.concatenate((derivative - transport, transport / volume_ratio,
                               [rates[r] for r, *_ in REACTIONS], forward, reverse))

    boundaries = {0.0, t_end}
    for gate in (params.pt_gate, params.oc_gate, params.dmt_gate):
        if gate.induction is not None and gate.induction.mode == "step":
            boundaries.update(value for value in (gate.induction.on_time, gate.induction.off_time)
                              if value is not None and 0 < value < t_end)
    evaluation = np.unique(np.concatenate((np.linspace(0.0, t_end, points), sorted(boundaries))))
    segments, times = [], []
    current = initial
    intervals = sorted(boundaries)
    for left, right in zip(intervals, intervals[1:]):
        sampled = evaluation[(evaluation >= left) & (evaluation <= right)]
        def segment_rhs(time, state):
            return rhs(np.nextafter(right, left) if time >= right else time, state)
        piece = solve_ivp(segment_rhs, (left, right), current, t_eval=sampled, method=method, rtol=rtol, atol=atol)
        if not piece.success:
            raise RuntimeError(piece.message)
        current = piece.y[:, -1]
        offset = 1 if segments else 0
        segments.append(piece.y[:, offset:])
        times.append(piece.t[offset:])
    solved = SimpleNamespace(t=np.concatenate(times), y=np.concatenate(segments, axis=1))
    raw_states = solved.y[:16]
    if float(raw_states.min()) < NUMERICAL_NEGATIVE_TOLERANCE:
        raise RuntimeError(f"numerical_negative_concentration_exceeds_tolerance:{raw_states.min():.3e}")
    states = np.where(raw_states < 0.0, 0.0, raw_states)
    fluxes = np.empty((10, solved.t.size))
    for column, (time, state) in enumerate(zip(solved.t, states.T, strict=True)):
        rates, _, _ = instantaneous(float(time), state)
        fluxes[:, column] = [rates[reaction_id] for reaction_id, *_ in REACTIONS]
    integrals = {reaction_id: float(solved.y[16 + index, -1]) for index, (reaction_id, *_rest) in enumerate(REACTIONS)}
    transport_integrals = {compound: {"total_outflow_cell_volume_equivalent": float(solved.y[26+i,-1]),
                                     "total_inflow_cell_volume_equivalent": float(solved.y[34+i,-1]),
                                     "net_outflow_cell_volume_equivalent": float(solved.y[26+i,-1]-solved.y[34+i,-1])}
                           for i,compound in enumerate(COMPOUNDS)}
    stoichiometry = np.zeros((8,10))
    for i,(_,_,substrate,product) in enumerate(REACTIONS):
        stoichiometry[_INDEX[substrate],i]=-1
        stoichiometry[_INDEX[product],i]=1
    reaction_change = stoichiometry @ solved.y[16:26]
    net_transport = solved.y[26:34] - solved.y[34:42]
    integral_error = float(max(np.max(np.abs(raw_states[:8]-initial[:8,None]-reaction_change+net_transport)),
                               np.max(np.abs(volume_ratio*(raw_states[8:16]-initial[8:16,None])-net_transport))))
    final_intracellular, final_extracellular = states[:8, -1], states[8:, -1]
    equivalents = states[:8] + volume_ratio * states[8:]
    final_15_total = float(equivalents[_INDEX["15"], -1])
    final_13_total = float(equivalents[_INDEX["13"], -1])
    net_15 = final_15_total - float(equivalents[_INDEX["15"], 0])
    net_13 = final_13_total - float(equivalents[_INDEX["13"], 0])
    initial_precursor = float(equivalents[:7, 0].sum())
    dmt_total = sum(integrals[f"R{index}"] for index in (4, 5, 6, 7))
    def fraction(numerator, denominator):
        return numerator / denominator if denominator > 0 else None
    net_pool = net_13 + net_15
    diagnostics = {
        "final_15_total": final_15_total,
        "final_13_total": final_13_total,
        "final_13_extracellular": float(final_extracellular[_INDEX["13"]]),
        "net_15_generated_cell_volume_equivalent": net_15,
        "net_13_generated_cell_volume_equivalent": net_13,
        "initial_convertible_backbone_cell_volume_equivalent": initial_precursor,
        "target_yield_fraction": fraction(net_15, initial_precursor),
        "branch_9_to_13_fraction": fraction(integrals["R5"], integrals["R2"] + integrals["R5"]),
        "q_9_to_13": fraction(integrals["R5"], integrals["R2"] + integrals["R5"]),
        "q_10_to_11": fraction(integrals["R3"], integrals["R3"] + integrals["R6"]),
        "final_13_intracellular_cell_volume": float(final_intracellular[_INDEX["13"]]),
        "final_15_intracellular_cell_volume": float(final_intracellular[_INDEX["15"]]),
        "final_13_extracellular_medium_volume": float(final_extracellular[_INDEX["13"]]),
        "final_15_extracellular_medium_volume": float(final_extracellular[_INDEX["15"]]),
        "remaining_initially_present_nonproduct_pool_cell_volume_equivalent": float(sum(equivalents[i,-1] for i in range(7) if initial_intracellular[COMPOUNDS[i]]>0 or initial_extracellular[COMPOUNDS[i]]>0)),
        "dmt_late_selectivity": fraction(integrals["R7"], dmt_total),
        "early_dmt_fraction": fraction(sum(integrals[f"R{index}"] for index in (4, 5, 6)), dmt_total),
        "oc_before_dmt_route_fraction": fraction(integrals["R7"], integrals["R7"] + integrals["R10"]),
        "side_product_fraction_13": fraction(net_13, net_pool) if net_13 >= 0 and net_15 >= 0 else None,
        "cumulative_R5_flux": integrals["R5"],
        "net_13_extracellular_accumulation_cell_volume_equivalent": volume_ratio * (float(final_extracellular[_INDEX["13"]]) - initial_extracellular["13"]),
        "mass_balance_error": float(np.max(np.abs(equivalents.sum(axis=0) - equivalents[:, 0].sum()))),
        "integrated_stoichiometry_max_abs_error": integral_error,
        "raw_minimum_concentration": float(raw_states.min()),
    }
    if params.transport.intracellular_volume_l is not None:
        diagnostics["backbone_amount_balance_error_umol"] = diagnostics["mass_balance_error"] * params.transport.intracellular_volume_l
    if integral_error > max(100*atol, 10*rtol*float(np.max(np.abs(solved.y)))):
        raise RuntimeError("integrated_stoichiometry_consistency_failed")
    return FullNetworkResult(solved.t, states[:8], states[8:], fluxes, integrals, diagnostics, params.unit_mode,
                             raw_states[:8], raw_states[8:], transport_integrals,
                             {"method": method,"rtol": rtol,"atol": atol,"integration_version":"adaptive-cumulative-v1"})
