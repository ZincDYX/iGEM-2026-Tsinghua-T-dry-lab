"""High-level contracts for the audited Galatea full M3/M4 workflow.

The module accepts explicitly supplied, provenance-labelled inputs.  It does
not invent project measurements and is intentionally separate from the
publication-reference adapter and legacy reduced M4 compatibility kernel.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .full_network import (
    COMPOUNDS, ENZYME_SUBSTRATES, EffectiveRecruitment, FullNetworkParameters,
    FullNetworkResult, PhaseDistribution, ReactionKinetics, TemporalGate,
    TransportParameters, effective_ratio_recruitment, phase_partition,
    simulate_full_network,
)


@dataclass(frozen=True)
class M3EffectiveRatioInputs:
    phi: float
    oc_total: float
    dmt_total: float
    slot_ratio_sh3_to_pdz: float
    total_recruited_fraction: float
    recruitment_bias_oc_vs_dmt: float = 1.0
    ptr_total: float = 0.0
    pt_total: float = 0.0
    metabolite_kp: dict[str, float] | None = None
    ptr_pt_phase_handling: Literal["dilute_only", "homogeneous_kp_1"] = "dilute_only"


@dataclass(frozen=True)
class M3EffectiveRatioResult:
    recruitment: EffectiveRecruitment
    enzyme_distributions: dict[str, PhaseDistribution]
    metabolite_kp: dict[str, float]
    assumptions: tuple[str, ...]


def run_m3_effective_ratio(inputs: M3EffectiveRatioInputs) -> M3EffectiveRatioResult:
    """Return M4-ready, mass-conserving OC/DMT phase concentrations."""
    if inputs.metabolite_kp is None or set(inputs.metabolite_kp) != set(COMPOUNDS):
        raise ValueError("m3_requires_partition_coefficients_for_compounds_8_to_15")
    if any(value <= 0 for value in inputs.metabolite_kp.values()):
        raise ValueError("m3_metabolite_partition_coefficients_must_be_positive")
    recruitment = effective_ratio_recruitment(
        oc_total=inputs.oc_total,
        dmt_total=inputs.dmt_total,
        phi=inputs.phi,
        slot_ratio_sh3_to_pdz=inputs.slot_ratio_sh3_to_pdz,
        total_recruited_fraction=inputs.total_recruited_fraction,
        recruitment_bias_oc_vs_dmt=inputs.recruitment_bias_oc_vs_dmt,
    )
    if inputs.ptr_pt_phase_handling == "dilute_only":
        if inputs.phi == 1 and (inputs.ptr_total > 0 or inputs.pt_total > 0):
            raise ValueError("dilute_only_ptr_pt_is_undefined_when_phi_is_one")
        denominator = 1.0 - inputs.phi
        ptr = PhaseDistribution(0.0, inputs.ptr_total / denominator if denominator else 0.0)
        pt = PhaseDistribution(0.0, inputs.pt_total / denominator if denominator else 0.0)
        assumption = "PTR/PT are nonrecruited and modeled as dilute-only enzymes."
    else:
        ptr = phase_partition(inputs.ptr_total, 1.0, inputs.phi)
        pt = phase_partition(inputs.pt_total, 1.0, inputs.phi)
        assumption = "PTR/PT are nonrecruited and modeled as homogeneous Kp=1 enzymes."
    return M3EffectiveRatioResult(
        recruitment=recruitment,
        enzyme_distributions={"PTR": ptr, "PT": pt, "OC": recruitment.oc, "DMT": recruitment.dmt},
        metabolite_kp=dict(inputs.metabolite_kp),
        assumptions=(
            "slot_ratio_sh3_to_pdz is an engineering capacity ratio, not measured binding thermodynamics.",
            "recruitment_bias_oc_vs_dmt is an explicit sensitivity parameter.",
            assumption,
        ),
    )


def load_author_native_reactions(path: Path) -> tuple[ReactionKinetics, ...]:
    """Load author-native reaction numbers without assigning a physical unit."""
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    expected = {f"R{index}" for index in range(1, 11)}
    if {row["reaction_id"] for row in rows} != expected:
        raise ValueError("author_native_reaction_network_is_incomplete")
    return tuple(
        ReactionKinetics(
            reaction_id=row["reaction_id"], enzyme=row["enzyme"], substrate=row["substrate"], product=row["product"],
            kcat=float(row["kcat_derived_author_native"]), km=float(row["Km_author_native"]),
        )
        for row in rows
    )


def run_galatea_full_m4(
    *, enzyme_distributions: dict[str, PhaseDistribution], phi: float, metabolite_kp: dict[str, float],
    reactions: tuple[ReactionKinetics, ...], initial_intracellular: dict[str, float],
    initial_extracellular: dict[str, float] | None = None, t_end: float,
    scenario: Literal[
        "homogeneous_constitutive", "homogeneous_published_like_temporal",
        "galatea_spatial", "galatea_spatiotemporal_ablation",
    ] = "galatea_spatial",
    transport: TransportParameters = TransportParameters(), dmt_gate: TemporalGate = TemporalGate(),
    pt_gate: TemporalGate = TemporalGate(), oc_gate: TemporalGate = TemporalGate(),
    activity_dense: dict[str, float] | None = None, activity_dilute: dict[str, float] | None = None,
    unit_mode: Literal["physical", "author_native_sensitivity"] = "physical",
    points: int = 501,
) -> FullNetworkResult:
    """Run full production M4 using M3 enzyme distributions and explicit Kp."""
    if set(metabolite_kp) != set(COMPOUNDS):
        raise ValueError("all_eight_metabolite_partition_coefficients_are_required")
    params = FullNetworkParameters(
        phi=phi,
        enzyme_distributions=enzyme_distributions,
        metabolite_kp=metabolite_kp,
        reactions=reactions,
        activity_dense=activity_dense or {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES},
        activity_dilute=activity_dilute or {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES},
        transport=transport,
        dmt_gate=dmt_gate,
        pt_gate=pt_gate,
        oc_gate=oc_gate,
        scenario=scenario,
        unit_mode=unit_mode,
    )
    return simulate_full_network(
        params,
        initial_intracellular=initial_intracellular,
        initial_extracellular=initial_extracellular,
        t_end=t_end,
        points=points,
    )
