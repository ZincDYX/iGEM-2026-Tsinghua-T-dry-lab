from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from igem_drylab.kinetics import (
    CascadeParameters,
    CompetitiveCascadeParameters,
    InductionGate,
    simulate_cascade,
    simulate_piecewise_induction,
)
from igem_drylab.parsers.vina import parse_vina_output


class DockingPenalty(BaseModel):
    """Negative binding screen; it is not an enzyme-activity measurement."""
    candidate_id: str
    reference_affinity_kcal_mol: float
    fusion_affinity_kcal_mol: float
    delta_delta_g_kcal_mol: float
    pose_available: bool = True
    binding_risk: str
    passes_negative_screen: bool
    notes: str = ""

    @property
    def passes(self) -> bool:
        return self.passes_negative_screen


class M4OdeScore(BaseModel):
    candidate_id: str
    product_final: float = Field(ge=0)
    intermediate_peak: float = Field(ge=0)
    relative_yield: float = Field(ge=0, le=1)
    leakage_proxy: float = Field(ge=0, le=1)
    recommendation: str


class M4PiecewiseOdeScore(BaseModel):
    candidate_id: str
    product_final: float = Field(ge=0)
    byproduct_final: float = Field(ge=0)
    intermediate_peak: float = Field(ge=0)
    relative_yield: float = Field(ge=0, le=1)
    leakage_fraction: float = Field(ge=0, le=1)
    observable_13_reduction: float = Field(ge=0)
    dmt_delay: float = Field(ge=0)
    recommendation: str
    bottleneck: str


def compute_docking_penalty(
    *,
    candidate_id: str,
    reference_vina_output: Path,
    fusion_vina_output: Path,
    allowed_loss_kcal_mol: float = 1.0,
) -> DockingPenalty:
    reference = parse_vina_output(reference_vina_output)
    fusion = parse_vina_output(fusion_vina_output)
    delta = fusion.best_affinity_kcal_mol - reference.best_affinity_kcal_mol
    risk = "low" if delta <= 0 else "moderate" if delta <= allowed_loss_kcal_mol else "high"
    return DockingPenalty(
        candidate_id=candidate_id,
        reference_affinity_kcal_mol=reference.best_affinity_kcal_mol,
        fusion_affinity_kcal_mol=fusion.best_affinity_kcal_mol,
        delta_delta_g_kcal_mol=round(delta, 3),
        binding_risk=risk,
        passes_negative_screen=delta <= allowed_loss_kcal_mol,
        notes="Vina affinity difference is a negative binding screen, not an activity multiplier.",
    )


def load_docking_penalties(path: Path) -> dict[str, DockingPenalty]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Docking penalties JSON must be a list or {'records': [...]}")
    penalties = [DockingPenalty.model_validate(item) for item in rows]
    return {item.candidate_id: item for item in penalties}


def score_m4_ode(
    *,
    candidate_id: str,
    params: CascadeParameters,
    docking_penalty: DockingPenalty | None = None,
    t_end: float = 24.0,
) -> M4OdeScore:
    # Docking can fail a construct's negative screen but cannot parameterize kinetics.
    result = simulate_cascade(params, t_end=t_end)
    product_final = float(result.product[-1])
    substrate_initial = float(result.substrate[0] + result.intermediate[0] + result.product[0])
    relative_yield = _clip01(product_final / substrate_initial) if substrate_initial > 0 else 0.0
    intermediate_peak = float(result.intermediate.max())
    leakage_proxy = _clip01(intermediate_peak / substrate_initial) if substrate_initial > 0 else 0.0
    if relative_yield >= 0.65 and leakage_proxy <= 0.25:
        recommendation = "test"
    elif relative_yield >= 0.35:
        recommendation = "iterate"
    else:
        recommendation = "drop"
    return M4OdeScore(
        candidate_id=candidate_id,
        product_final=round(product_final, 6),
        intermediate_peak=round(intermediate_peak, 6),
        relative_yield=round(relative_yield, 3),
        leakage_proxy=round(leakage_proxy, 3),
        recommendation=recommendation,
    )


def score_m4_piecewise_ode(
    *,
    candidate_id: str,
    params: CompetitiveCascadeParameters,
    oc_gate: InductionGate = InductionGate(on_time=0.0, basal=0.0, induced=1.0),
    dmt_gate: InductionGate = InductionGate(on_time=4.0, basal=0.0, induced=1.0),
    docking_penalty: DockingPenalty | None = None,
    initial: tuple[float, float, float, float] = (10.0, 0.0, 0.0, 0.0),
    t_end: float = 24.0,
) -> M4PiecewiseOdeScore:
    delayed = simulate_piecewise_induction(
        params,
        oc_gate=oc_gate,
        dmt_gate=dmt_gate,
        initial=initial,
        t_end=t_end,
    )
    baseline = simulate_piecewise_induction(
        params,
        oc_gate=InductionGate(on_time=oc_gate.on_time, basal=oc_gate.basal, induced=oc_gate.induced, mode=oc_gate.mode),
        dmt_gate=InductionGate(on_time=0.0, basal=dmt_gate.basal, induced=dmt_gate.induced, mode=dmt_gate.mode),
        initial=initial,
        t_end=t_end,
    )
    product_final = float(delayed.product[-1])
    byproduct_final = float(delayed.byproduct[-1])
    substrate_initial = float(sum(initial))
    relative_yield = _clip01(product_final / substrate_initial) if substrate_initial > 0 else 0.0
    leakage_fraction = _clip01(byproduct_final / (product_final + byproduct_final)) if product_final + byproduct_final > 0 else 0.0
    baseline_byproduct = float(baseline.byproduct[-1])
    if byproduct_final <= 0:
        observable_13_reduction = baseline_byproduct / 1e-12 if baseline_byproduct > 0 else 1.0
    else:
        observable_13_reduction = baseline_byproduct / byproduct_final
    intermediate_peak = float(delayed.intermediate.max())
    dmt_delay = max(0.0, dmt_gate.on_time - oc_gate.on_time)
    if relative_yield >= 0.6 and leakage_fraction <= 0.2:
        recommendation = "test"
    elif relative_yield >= 0.25 and observable_13_reduction >= 1.2:
        recommendation = "iterate"
    else:
        recommendation = "drop"
    bottleneck = _piecewise_bottleneck(
        relative_yield=relative_yield,
        leakage_fraction=leakage_fraction,
        intermediate_peak=intermediate_peak,
        substrate_initial=substrate_initial,
    )
    return M4PiecewiseOdeScore(
        candidate_id=candidate_id,
        product_final=round(product_final, 6),
        byproduct_final=round(byproduct_final, 6),
        intermediate_peak=round(intermediate_peak, 6),
        relative_yield=round(relative_yield, 3),
        leakage_fraction=round(leakage_fraction, 3),
        observable_13_reduction=round(observable_13_reduction, 3),
        dmt_delay=round(dmt_delay, 3),
        recommendation=recommendation,
        bottleneck=bottleneck,
    )


def _piecewise_bottleneck(
    *,
    relative_yield: float,
    leakage_fraction: float,
    intermediate_peak: float,
    substrate_initial: float,
) -> str:
    if leakage_fraction > 0.35:
        return "dmt_leakage"
    if substrate_initial > 0 and intermediate_peak / substrate_initial > 0.45 and relative_yield < 0.5:
        return "dmt_late_or_dmt_low"
    if relative_yield < 0.25:
        return "oc_or_partition_low"
    return "balanced"


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
