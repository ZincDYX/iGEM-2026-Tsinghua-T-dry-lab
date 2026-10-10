"""Typed semantic boundary between an LLM and deterministic execution planning."""
from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    """String-valued enums with stable str() on the supported Python 3.10 floor."""
    def __str__(self) -> str:
        return self.value

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Annotated, Union


class ScientificActionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


class InspectProjectAction(ScientificActionBase):
    kind: Literal["inspect_project"]


class RetrieveEvidenceAction(ScientificActionBase):
    kind: Literal["retrieve_evidence"]
    query: str = Field(min_length=1)
    source_scope: Literal["project_registry", "registered_artifacts"]


class PrepareNodeAction(ScientificActionBase):
    kind: Literal["prepare_node"]
    tool_id: str
    input_refs: list[str]


class SubmitJobAction(ScientificActionBase):
    kind: Literal["submit_job"]
    reviewed_proposal_id: str


class InspectJobAction(ScientificActionBase):
    kind: Literal["inspect_job"]
    run_id: str


class EvaluateResultAction(ScientificActionBase):
    kind: Literal["evaluate_result"]
    result_ref: str
    metric: Literal["recorded_stage_status", "recorded_mass_balance", "recorded_applicability"]


class ProposeExperimentAction(ScientificActionBase):
    kind: Literal["propose_experiment"]
    hypothesis: str = Field(min_length=1)
    controls: list[str] = Field(min_length=1)
    observable: str = Field(min_length=1)
    refutation_criterion: str = Field(min_length=1)
    requires_human_review: Literal[True] = True


class WaitAction(ScientificActionBase):
    kind: Literal["wait"]
    pending_refs: list[str] = Field(min_length=1)


class FinishAction(ScientificActionBase):
    kind: Literal["finish"]
    outcome: Literal["available_work_completed", "human_input_required", "no_compute_requested"]


ScientificAction = Annotated[Union[InspectProjectAction,RetrieveEvidenceAction,PrepareNodeAction,SubmitJobAction,
    InspectJobAction,EvaluateResultAction,ProposeExperimentAction,WaitAction,FinishAction],Field(discriminator="kind")]


class ChangeType(StringEnum):
    parameter_update = "parameter_update"
    scaffold_capacity_update = "scaffold_capacity_update"
    construct_sequence_update = "construct_sequence_update"
    fusion_architecture_update = "fusion_architecture_update"
    timecourse_update = "timecourse_update"
    artifact_update = "artifact_update"
    interpretation_only = "interpretation_only"
    new_design_request = "new_design_request"
    unknown = "unknown"


class Stage(StringEnum):
    m1 = "m1"; m2 = "m2"; m3 = "m3"; m4 = "m4"; m5 = "m5"


class ArtifactAction(StringEnum):
    reuse = "reuse"; validate = "validate"; invalidate = "invalidate"; recompute = "recompute"; none = "none"


class EvidenceAction(StringEnum):
    none = "none"; use_existing = "use_existing"; search_local_evidence = "search_local_evidence"; request_measurement = "request_measurement"; human_review = "human_review"


class MeasurementSource(StringEnum):
    wetlab = "wetlab"; literature = "literature"; existing_artifact = "existing_artifact"; user_declared = "user_declared"; unknown = "unknown"


class RequestedOutcome(StringEnum):
    recompute = "recompute"; calibrate = "calibrate"; interpret = "interpret"; design = "design"; validate = "validate"; resolve_missing_input = "resolve_missing_input"


class ScientificConstraint(StringEnum):
    do_not_rerun_unaffected_structural_stages = "do_not_rerun_unaffected_structural_stages"
    docking_not_kinetic_modifier = "docking_not_kinetic_modifier"
    capacity_not_measured_abundance = "capacity_not_measured_abundance"
    author_native_not_physical_titer = "author_native_not_physical_titer"
    sensitivity_not_causality = "sensitivity_not_causality"
    do_not_invent_parameters = "do_not_invent_parameters"
    invalid_artifact_never_reuse = "invalid_artifact_never_reuse"


class SemanticDecision(BaseModel):
    """LLM-proposed semantic interpretation, not an executable tool plan."""
    model_config = ConfigDict(extra="forbid")
    change_types: list[ChangeType] = Field(default_factory=list)
    changed_entities: list[str] = Field(default_factory=list)
    measurement_source: MeasurementSource = MeasurementSource.unknown
    requested_outcome: RequestedOutcome
    artifact_action: ArtifactAction
    missing_inputs: list[str] = Field(default_factory=list)
    evidence_action: EvidenceAction
    requires_human_review: bool
    requires_new_compute: bool
    scientific_constraints: list[ScientificConstraint] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    scientific_actions: list[ScientificAction] = Field(default_factory=list)


# Compatibility name for v3 callers.  It has v4 semantics and intentionally
# no LLM-authoritative stage field.
PlanningDecision = SemanticDecision
