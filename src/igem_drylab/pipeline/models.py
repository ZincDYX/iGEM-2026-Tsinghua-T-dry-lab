from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ScientificStatus = Literal["valid", "insufficient_data", "invalid_input", "failed"]
DataQuality = Literal["measured", "fitted", "literature", "predicted", "heuristic", "demo_fixture", "mixed"]


class ScientificResult(BaseModel):
    """Common uncertainty contract for all stage outputs."""

    status: ScientificStatus = "valid"
    data_quality: DataQuality = "heuristic"
    missing_inputs: list[str] = Field(default_factory=list)
    recommended_next_action: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    parameter_ids: list[str] = Field(default_factory=list)
    provenance_summary: dict[str, int] = Field(default_factory=dict)


class StageOutput(BaseModel):
    stage: str
    directory: Path
    json_file: Path
    csv_file: Path
    record_count: int


class PipelineManifest(BaseModel):
    run_id: str
    run_dir: Path
    stages: list[StageOutput]


class M1Candidate(ScientificResult):
    candidate_id: str
    construct_id: str
    construct_definition: dict[str, Any]
    scaffold_id: str | None = None
    linker_id: str | None = None
    idr_id: str | None = None
    linker_features: dict[str, Any] | None = None
    formula_version: str | None = None
    rule_version: str | None = None
    feature_definitions_sha256: str | None = None
    sequence_sha256: str | None = None
    sequence_screen_verdict: Literal["pass", "review", "reject", "blocked"] | None = None
    missing_predictor_evidence: list[str] = Field(default_factory=list)
    screen_flags: list[str] = Field(default_factory=list)
    engineering_priority_score: float | None = Field(default=None, ge=0, le=1)
    recommended_for_m2: bool = False
    notes: str = ""


class M2FusionAssessment(ScientificResult):
    candidate_id: str
    construct_id: str
    construct_definition: dict[str, Any]
    structure_model: str | None = None
    structure_source_tool: str | None = None
    structure_source_tool_version: str | None = None
    structure_artifact_path: str | None = None
    structure_artifact_sha256: str | None = None
    reference_structure_id: str | None = None
    reference_artifact_sha256: str | None = None
    geometry_input_sha256: str | None = None
    sasa_configuration_hash: str | None = None
    clash_rule_provenance: str | None = None
    available_metrics: list[str] = Field(default_factory=list)
    missing_metrics: list[str] = Field(default_factory=list)
    screen_verdict: Literal["pass", "review", "reject", "blocked"] = "blocked"
    confidence_gate: Literal["high", "medium", "low", "missing"] = "missing"
    formula_version: str | None = None
    core_ca_rmsd_angstrom: float | None = Field(default=None, ge=0)
    heuristic_structure_risk: float | None = Field(default=None, ge=0, le=1)
    pocket_sasa_retention: float | None = Field(default=None, ge=0)
    pocket_rmsd_angstrom: float | None = Field(default=None, ge=0)
    tail_pocket_min_distance_angstrom: float | None = Field(default=None, ge=0)
    clash_count: int | None = Field(default=None, ge=0)
    clash_cutoff_angstrom: float | None = Field(default=None, gt=0)
    recommended_for_m3: bool = False
    threshold_origin: str = "M2-V2-2026-09-27-project-screening-rule"
    notes: str = ""


class M3ConcentrationAssessment(ScientificResult):
    candidate_id: str
    construct_id: str
    concentrations: dict[str, dict[str, Any]] = Field(default_factory=dict)
    dense_oc_dmt_ratio: float | None = Field(default=None, ge=0)
    whole_cell_oc_dmt_ratio: float | None = Field(default=None, ge=0)
    fraction_in_dense: dict[str, float] = Field(default_factory=dict)
    binding_recruitment_status: Literal["not_requested", "valid", "insufficient_data"] = "not_requested"
    binding_recruited_fraction: dict[str, float] = Field(default_factory=dict)
    site_occupancy: dict[str, float] = Field(default_factory=dict)
    recommended_for_m4: bool = False
    m4_candidate_context: M4CandidateContext | None = None
    notes: str = ""


class M4CandidateContext(BaseModel):
    """Mass-conserving candidate-specific enzyme distribution passed from M3 to M4."""

    candidate_id: str
    construct_id: str
    condition_id: str
    phi: float = Field(ge=0, lt=1)
    enzyme_distribution: dict[str, dict[str, float]]
    metabolite_partition_coefficients: dict[str, float] = Field(default_factory=dict)
    binding_recruited_fraction: dict[str, float] = Field(default_factory=dict)
    site_occupancy: dict[str, float] = Field(default_factory=dict)
    parameter_ids: list[str] = Field(default_factory=list)
    provenance_summary: dict[str, int] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)


class M4ReactionPrediction(ScientificResult):
    candidate_id: str
    construct_id: str
    condition_id: str
    target_product: str
    final_15: float | None = Field(default=None, ge=0)
    final_13: float | None = Field(default=None, ge=0)
    side_product_fraction_13: float | None = Field(default=None, ge=0, le=1)
    # Deprecated compatibility alias.  This model has no extracellular export term.
    leakage_fraction: float | None = Field(default=None, ge=0, le=1)
    productivity: float | None = Field(default=None, ge=0)
    recommendation: Literal["drop", "iterate", "test", "insufficient_data"] = "insufficient_data"
    baseline_comparison: dict[str, float] = Field(default_factory=dict)
    bottleneck: str = "insufficient_data"
    trajectory_artifact: Path | None = None
    candidate_context: M4CandidateContext | None = None
    simulation_inputs: dict[str, Any] = Field(default_factory=dict)
    recommendation_evidence: list[str] = Field(default_factory=list)
    flux_integrals: dict[str, float] = Field(default_factory=dict)
    mechanistic_diagnostics: dict[str, float] = Field(default_factory=dict)
    notes: str = ""


class M5FeedbackAssessment(ScientificResult):
    experiment_id: str
    construct_id: str
    condition_id: str = "unresolved"
    replicate_id: str = "unresolved"
    qc_passed: bool | None = None
    qc_flags: list[str] = Field(default_factory=list)
    diagnosis: str | None = None
    prediction_residual: float | None = None
    trend_agreement: bool | None = None
    replicate_variation: float | None = None
    fit: dict[str, Any] | None = None
    metabolite_comparisons: dict[str, Any] = Field(default_factory=dict)
    diagnosis_evidence: dict[str, Any] = Field(default_factory=dict)
    fitted_parameter_candidate: dict[str, Any] | None = None
    next_measurement: str | None = None
    notes: str = ""
