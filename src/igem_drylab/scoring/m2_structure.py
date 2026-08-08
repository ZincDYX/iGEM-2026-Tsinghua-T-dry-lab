from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

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
    status: Literal["valid", "insufficient_data"]
    available_metrics: list[str]
    missing_metrics: list[str]
    activity_risk: float | None = Field(default=None, ge=0, le=1)
    clash_risk: float | None = Field(default=None, ge=0, le=1)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    heuristic_structure_risk: float | None = Field(default=None, ge=0, le=1)
    recommended_for_m3: bool
    threshold_origin: str = "project_heuristic"
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

    present = [name for name, value in metrics.model_dump().items() if value is not None and name not in {"candidate_id", "notes"}]
    required = {"sasa_retention", "pocket_rmsd_angstrom", "clash_count", "iptm", "mean_plddt"}
    missing = sorted(required - set(present))
    if missing:
        return M2StructureScore(
            candidate_id=metrics.candidate_id, status="insufficient_data", available_metrics=present, missing_metrics=missing,
            recommended_for_m3=False, reasons=["missing_required_structure_metrics"],
        )
    activity_risk = _average(activity_terms)
    clash_risk = _average(clash_terms)
    confidence_score = _average(confidence_terms)
    risk = _clip01(0.45 * activity_risk + 0.25 * clash_risk + 0.30 * (1 - confidence_score))
    return M2StructureScore(
        candidate_id=metrics.candidate_id,
        status="valid",
        available_metrics=present,
        missing_metrics=[],
        activity_risk=round(activity_risk, 3),
        clash_risk=round(clash_risk, 3),
        confidence_score=round(confidence_score, 3),
        heuristic_structure_risk=round(risk, 3),
        recommended_for_m3=activity_risk <= 0.45 and clash_risk <= 0.45,
        reasons=reasons or ["passed_rule_based_structure_screen"],
    )


def _average(values: list[float]) -> float:
    if not values:
        raise ValueError("required structure metric group was unexpectedly empty")
    return sum(values) / len(values)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
