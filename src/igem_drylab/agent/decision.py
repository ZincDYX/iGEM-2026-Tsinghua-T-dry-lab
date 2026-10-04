"""Typed semantic boundary between an LLM and deterministic execution planning."""
from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    """String-valued enums with stable str() on the supported Python 3.10 floor."""
    def __str__(self) -> str:
        return self.value

from pydantic import BaseModel, ConfigDict, Field


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


# Compatibility name for v3 callers.  It has v4 semantics and intentionally
# no LLM-authoritative stage field.
PlanningDecision = SemanticDecision
