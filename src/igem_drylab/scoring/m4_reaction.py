from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from igem_drylab.kinetics import CascadeParameters, simulate_cascade
from igem_drylab.parsers.vina import parse_vina_output


class DockingPenalty(BaseModel):
    candidate_id: str
    reference_affinity_kcal_mol: float
    fusion_affinity_kcal_mol: float
    delta_delta_g_kcal_mol: float
    activity_multiplier: float = Field(ge=0, le=1)
    passes: bool


class M4OdeScore(BaseModel):
    candidate_id: str
    product_final: float = Field(ge=0)
    intermediate_peak: float = Field(ge=0)
    relative_yield: float = Field(ge=0, le=1)
    leakage_proxy: float = Field(ge=0, le=1)
    recommendation: str


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
    multiplier = _clip01(1.0 - max(0.0, delta) / 4.0)
    return DockingPenalty(
        candidate_id=candidate_id,
        reference_affinity_kcal_mol=reference.best_affinity_kcal_mol,
        fusion_affinity_kcal_mol=fusion.best_affinity_kcal_mol,
        delta_delta_g_kcal_mol=round(delta, 3),
        activity_multiplier=round(multiplier, 3),
        passes=delta <= allowed_loss_kcal_mol,
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
    multiplier = docking_penalty.activity_multiplier if docking_penalty is not None else 1.0
    adjusted = CascadeParameters(
        **{
            **params.__dict__,
            "activity_ratio_oc": params.activity_ratio_oc * multiplier,
            "activity_ratio_dmt": params.activity_ratio_dmt * multiplier,
        }
    )
    result = simulate_cascade(adjusted, t_end=t_end)
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


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
