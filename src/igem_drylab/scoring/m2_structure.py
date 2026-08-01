from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class M2StructureMetrics(BaseModel):
    candidate_id: str
    sasa_retention: float | None = Field(default=None, ge=0)
    pocket_rmsd_angstrom: float | None = Field(default=None, ge=0)
    mean_interdomain_pae: float | None = Field(default=None, ge=0)
    iptm: float | None = Field(default=None, ge=0, le=1)
    mean_plddt: float | None = Field(default=None, ge=0, le=100)
    interface_contact_count: int | None = Field(default=None, ge=0)
    clash_count: int | None = Field(default=None, ge=0)
    notes: str = ""


class M2StructureScore(BaseModel):
    candidate_id: str
    activity_risk: float = Field(ge=0, le=1)
    clash_risk: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    m2_score: float = Field(ge=0, le=1)
    recommended_for_m3: bool
    reasons: list[str]


def load_m2_structure_metrics(path: Path) -> dict[str, M2StructureMetrics]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("M2 metrics JSON must be a list or {'records': [...]}")
    metrics = [M2StructureMetrics.model_validate(item) for item in rows]
    return {item.candidate_id: item for item in metrics}


def score_m2_structure(metrics: M2StructureMetrics) -> M2StructureScore:
    """Score structural compatibility using transparent negative screening rules.

    The defaults encode the current project policy: >15% pocket SASA loss and
    >1.5 A pocket RMSD are strong activity risks. The weights are intentionally
    simple and should be calibrated after wet-lab data exists.
    """
    reasons: list[str] = []
    activity_terms: list[float] = []
    clash_terms: list[float] = []
    confidence_terms: list[float] = []

    if metrics.sasa_retention is not None:
        sasa_risk = _clip01((0.85 - metrics.sasa_retention) / 0.35)
        activity_terms.append(sasa_risk)
        if metrics.sasa_retention < 0.85:
            reasons.append("pocket_sasa_loss_over_15_percent")
    if metrics.pocket_rmsd_angstrom is not None:
        rmsd_risk = _clip01((metrics.pocket_rmsd_angstrom - 0.5) / 1.5)
        activity_terms.append(rmsd_risk)
        if metrics.pocket_rmsd_angstrom > 1.5:
            reasons.append("pocket_rmsd_over_1_5_angstrom")
    if metrics.clash_count is not None:
        clash_risk = _clip01(metrics.clash_count / 10)
        clash_terms.append(clash_risk)
        if metrics.clash_count > 0:
            reasons.append("steric_clashes_detected")
    if metrics.interface_contact_count is not None:
        contact_risk = 1.0 - _clip01(metrics.interface_contact_count / 20)
        clash_terms.append(0.35 * contact_risk)
        if metrics.interface_contact_count == 0:
            reasons.append("no_chain_interface_contacts")
    if metrics.iptm is not None:
        confidence_terms.append(metrics.iptm)
        if metrics.iptm < 0.5:
            reasons.append("low_inter_chain_confidence")
    if metrics.mean_plddt is not None:
        confidence_terms.append(_clip01(metrics.mean_plddt / 100))
        if metrics.mean_plddt < 70:
            reasons.append("low_local_confidence")
    if metrics.mean_interdomain_pae is not None:
        # High PAE between flexibly linked domains is not automatically bad.
        # Penalize only suspiciously rigid or extremely uncertain assemblies.
        if metrics.mean_interdomain_pae < 5:
            confidence_terms.append(0.65)
            reasons.append("very_low_domain_pae_possible_rigid_sticking")
        elif metrics.mean_interdomain_pae > 30:
            confidence_terms.append(0.55)
            reasons.append("very_high_domain_pae_low_global_placement_confidence")
        else:
            confidence_terms.append(0.85)

    activity_risk = _average(activity_terms, default=0.25)
    clash_risk = _average(clash_terms, default=0.20)
    confidence_score = _average(confidence_terms, default=0.65)
    score = _clip01(0.45 * (1 - activity_risk) + 0.25 * (1 - clash_risk) + 0.30 * confidence_score)
    return M2StructureScore(
        candidate_id=metrics.candidate_id,
        activity_risk=round(activity_risk, 3),
        clash_risk=round(clash_risk, 3),
        confidence_score=round(confidence_score, 3),
        m2_score=round(score, 3),
        recommended_for_m3=score >= 0.55 and activity_risk <= 0.45 and clash_risk <= 0.45,
        reasons=reasons or ["passed_rule_based_structure_screen"],
    )


def _average(values: list[float], *, default: float) -> float:
    return default if not values else sum(values) / len(values)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
