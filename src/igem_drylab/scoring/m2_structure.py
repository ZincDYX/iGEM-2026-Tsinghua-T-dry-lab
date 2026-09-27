"""M2 V2 confidence-gated structural negative screening.

This module intentionally does not synthesize a weighted 0--1 structure score.
It preserves the measured/computed metrics and applies only the explicit
2026-09-27 project rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


M2_FORMULA_VERSION = "m2-v2-2026-09-27"


class M2StructureMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    source_tool: str | None = None
    source_tool_version: str | None = None
    source_model: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    reference_structure_id: str | None = None
    reference_artifact_sha256: str | None = None
    geometry_input_sha256: str | None = None
    sasa_configuration_hash: str | None = None
    clash_rule_provenance: str | None = None
    pocket_definition_source_ref: str | None = None
    residue_mapping_source_ref: str | None = None
    pocket_residue_ids: list[int] = Field(default_factory=list)
    core_residue_ids: list[int] = Field(default_factory=list)
    formula_version: Literal["m2-v2-2026-09-27"] = M2_FORMULA_VERSION

    # Q1 metrics. Existing field names remain readable for old result bundles.
    core_ca_rmsd_angstrom: float | None = Field(default=None, ge=0)
    sasa_retention: float | None = Field(default=None, ge=0)
    pocket_rmsd_angstrom: float | None = Field(default=None, ge=0)
    tail_pocket_min_distance_angstrom: float | None = Field(default=None, ge=0)
    mean_plddt: float | None = Field(default=None, ge=0, le=100)
    core_mean_plddt: float | None = Field(default=None, ge=0, le=100)
    pocket_mean_plddt: float | None = Field(default=None, ge=0, le=100)

    # Q2/Q3 explicit observations. ``buried`` must come from an audited
    # same-residue/same-FreeSASA-configuration comparison.
    ligand_sasa_retention: float | None = Field(default=None, ge=0)
    recruitment_domain_sasa_retention: float | None = Field(default=None, ge=0)
    ligand_buried: bool | None = None
    recruitment_domain_buried: bool | None = None
    scaffold_interface_disrupted: bool | None = None

    # Reviewed M2 -> M3 geometry contract. These remain predicted geometry,
    # not measured binding probabilities.
    s_sh3: int | None = Field(default=None, ge=0)
    s_pdz: int | None = Field(default=None, ge=0)
    eta_acc_sh3: float | None = Field(default=None, ge=0, le=1)
    eta_acc_pdz: float | None = Field(default=None, ge=0, le=1)
    eta_bind_sh3: float | None = Field(default=None, ge=0, le=1)
    eta_bind_pdz: float | None = Field(default=None, ge=0, le=1)
    site_count_basis: Literal["scaffold_monomer", "complete_assembly"] | None = None
    joint_occupancy_independent: bool | None = None
    m2_geometry_id: str | None = None
    v_scaffold_nm3: float | None = Field(default=None, gt=0)
    v_enzyme_nm3: float | None = Field(default=None, gt=0)
    volume_method: str | None = None

    # Q4 collision evidence. One rigid-model clash count is never enough for
    # rejection; persistence and direct functional occlusion are explicit.
    clash_count: int | None = Field(default=None, ge=0)
    clash_cutoff_angstrom: float | None = Field(default=None, gt=0)
    independent_conformation_count: int | None = Field(default=None, ge=1)
    severe_clash_conformation_count: int | None = Field(default=None, ge=0)
    persistent_severe_clash: bool | None = None
    direct_pocket_occlusion: bool | None = None

    # Confidence/diagnostic fields; high inter-domain PAE is not a failure for
    # a flexible linker and ipTM is not an activity proxy.
    mean_interdomain_pae: float | None = Field(default=None, ge=0)
    iptm: float | None = Field(default=None, ge=0, le=1)
    interface_contact_count: int | None = Field(default=None, ge=0)
    docking_delta_kcal_mol: float | None = None
    docking_configuration_hash: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _validate_collision_evidence(self) -> "M2StructureMetrics":
        if self.clash_count is not None and self.clash_cutoff_angstrom is None:
            raise ValueError("clash_count_requires_explicit_clash_cutoff_angstrom")
        if self.severe_clash_conformation_count is not None:
            if self.independent_conformation_count is None:
                raise ValueError("severe_clash_count_requires_independent_conformation_count")
            if self.severe_clash_conformation_count > self.independent_conformation_count:
                raise ValueError("severe_clash_conformation_count_exceeds_total")
        if self.persistent_severe_clash is True and (
            self.independent_conformation_count is None
            or self.severe_clash_conformation_count != self.independent_conformation_count
        ):
            raise ValueError("persistent_severe_clash_requires_all_independent_conformations")
        return self


class M2StructureScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    status: Literal["valid", "insufficient_data", "invalid_input"]
    verdict: Literal["pass", "review", "reject", "blocked"]
    confidence_gate: Literal["high", "medium", "low", "missing"]
    available_metrics: list[str]
    missing_metrics: list[str]
    recommended_for_m3: bool
    threshold_origin: str = "M2-V2-2026-09-27-project-screening-rule"
    formula_version: Literal["m2-v2-2026-09-27"] = M2_FORMULA_VERSION
    reasons: list[str]
    # Retired composite fields stay nullable for output compatibility. They are
    # never used in the decision.
    activity_risk: None = None
    clash_risk: None = None
    confidence_score: None = None
    heuristic_structure_risk: None = None


def load_m2_structure_metrics(path: Path) -> dict[str, M2StructureMetrics]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("M2 metrics JSON must be a list or {'records': [...]}")
    metrics = [M2StructureMetrics.model_validate(item) for item in rows]
    if len({item.candidate_id for item in metrics}) != len(metrics):
        raise ValueError("duplicate_m2_metric_candidate_id")
    return {item.candidate_id: item for item in metrics}


def score_m2_structure(metrics: M2StructureMetrics) -> M2StructureScore:
    """Apply confidence gates before the explicit M2 V2 negative rules."""

    excluded = {
        "candidate_id",
        "notes",
        "source_tool",
        "source_tool_version",
        "source_model",
        "artifact_path",
        "artifact_sha256",
        "reference_structure_id",
        "reference_artifact_sha256",
        "geometry_input_sha256",
        "sasa_configuration_hash",
        "clash_rule_provenance",
        "pocket_definition_source_ref",
        "residue_mapping_source_ref",
        "formula_version",
        "m2_geometry_id",
        "site_count_basis",
        "volume_method",
    }
    present = sorted(
        name
        for name, value in metrics.model_dump().items()
        if value not in (None, [], "") and name not in excluded
    )
    required = {
        "core_ca_rmsd_angstrom",
        "sasa_retention",
        "pocket_rmsd_angstrom",
        "clash_count",
        "clash_cutoff_angstrom",
    }
    missing = sorted(required - set(present))
    confidence_value = _geometry_plddt(metrics)
    confidence_gate = _confidence_gate(confidence_value)
    if confidence_value is None:
        missing.append("core_or_pocket_pLDDT")
    missing = sorted(set(missing))
    if missing:
        return M2StructureScore(
            candidate_id=metrics.candidate_id,
            status="insufficient_data",
            verdict="blocked",
            confidence_gate=confidence_gate,
            available_metrics=present,
            missing_metrics=missing,
            recommended_for_m3=False,
            reasons=["missing_required_structure_metrics"],
        )

    reasons: list[str] = []
    review: list[str] = []
    reject: list[str] = []

    if confidence_gate == "low":
        return M2StructureScore(
            candidate_id=metrics.candidate_id,
            status="insufficient_data",
            verdict="blocked",
            confidence_gate="low",
            available_metrics=present,
            missing_metrics=[],
            recommended_for_m3=False,
            reasons=["pLDDT_below_50_geometry_not_interpretable"],
        )
    if confidence_gate == "medium":
        review.append("pLDDT_50_to_70_metrics_are_reference_only")

    # Threshold rejection is permitted only for high-confidence folded regions.
    if metrics.sasa_retention is not None and metrics.sasa_retention < 0.70:
        (reject if confidence_gate == "high" else review).append("pocket_sasa_retention_below_0_70")
    if metrics.core_ca_rmsd_angstrom is not None and metrics.core_ca_rmsd_angstrom > 4.0:
        (reject if confidence_gate == "high" else review).append("core_CA_RMSD_over_4_angstrom")
    if metrics.ligand_buried is True:
        (reject if confidence_gate == "high" else review).append("recruitment_ligand_buried")
    if metrics.recruitment_domain_buried is True:
        (reject if confidence_gate == "high" else review).append("recruitment_domain_binding_site_buried")
    if metrics.scaffold_interface_disrupted is True:
        (reject if confidence_gate == "high" else review).append("FTH1_oligomer_interface_disrupted")

    if metrics.clash_count and metrics.clash_count > 0:
        if (
            confidence_gate == "high"
            and metrics.persistent_severe_clash is True
            and metrics.direct_pocket_occlusion is True
        ):
            reject.append("persistent_high_confidence_severe_clash_directly_occludes_functional_site")
        else:
            review.append("rigid_model_clash_requires_independent_conformation_review")

    if metrics.mean_interdomain_pae is not None and metrics.mean_interdomain_pae > 30:
        review.append("high_interdomain_PAE_position_is_uncertain_not_failed")
    if metrics.docking_delta_kcal_mol is not None:
        if metrics.docking_configuration_hash is None:
            review.append("docking_delta_missing_shared_configuration_hash")
        else:
            reasons.append("docking_delta_is_pose_screen_only_not_Kd_kcat_or_activity")

    reasons.extend(review)
    reasons.extend(reject)
    if reject:
        verdict: Literal["pass", "review", "reject", "blocked"] = "reject"
        status: Literal["valid", "insufficient_data", "invalid_input"] = "valid"
    elif review:
        verdict = "review"
        status = "valid"
    else:
        verdict = "pass"
        status = "valid"
        reasons.append("passed_M2_V2_confidence_gated_negative_screen")
    return M2StructureScore(
        candidate_id=metrics.candidate_id,
        status=status,
        verdict=verdict,
        confidence_gate=confidence_gate,
        available_metrics=present,
        missing_metrics=[],
        recommended_for_m3=verdict == "pass",
        reasons=reasons,
    )


def _geometry_plddt(metrics: M2StructureMetrics) -> float | None:
    values = [value for value in (metrics.core_mean_plddt, metrics.pocket_mean_plddt) if value is not None]
    if values:
        return min(values)
    return metrics.mean_plddt


def _confidence_gate(value: float | None) -> Literal["high", "medium", "low", "missing"]:
    if value is None:
        return "missing"
    if value > 70:
        return "high"
    if value >= 50:
        return "medium"
    return "low"
