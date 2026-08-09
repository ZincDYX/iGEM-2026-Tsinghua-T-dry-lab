"""Serializable project state shared by workflow and agent modes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constructs import ConstructRecord
from .parameters import ParameterRecord, ParameterRegistry, resolve_requirement
from .parameters.requirements import ParameterRequirement, m3_requirements, m4_requirements, requirements_for_stage
from .pipeline.config import ExperimentalContext


class ProjectState(BaseModel):
    project_id: str
    constructs: list[ConstructRecord] = Field(default_factory=list)
    approved_parameters: list[ParameterRecord] = Field(default_factory=list)
    experimental_context: ExperimentalContext = Field(default_factory=ExperimentalContext)
    available_artifacts: list[str] = Field(default_factory=list)
    completed_stages: list[str] = Field(default_factory=list)
    pending_measurements: list[str] = Field(default_factory=list)
    wetlab_results: list[str] = Field(default_factory=list)
    hypotheses: list[dict[str, object]] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    requirements_by_stage: dict[str, list[ParameterRequirement]] = Field(default_factory=lambda: {"m3": m3_requirements(), "m4": m4_requirements()})

    def missing_inputs(self, stage: str, *, allow_assumptions: bool = False, construct_id: str | None = None, condition_id: str | None = None, enable_degradation: bool = False, require_provenance: bool = False) -> list[str]:
        requirements = self.requirements_by_stage.get(stage, [])
        registry = ParameterRegistry(self.approved_parameters)
        return [item.name for item in requirements if item.blocking and resolve_requirement(registry, item, self.experimental_context, allow_assumptions=allow_assumptions, construct_id=construct_id, condition_id=condition_id, require_provenance=require_provenance).status != "resolved"]

    @classmethod
    def from_project(cls, project: object) -> "ProjectState":
        return cls(project_id=project.run.id, constructs=project.inputs.construct_records, approved_parameters=[item for item in project.parameters if item.review_status == "approved"], experimental_context=project.experimental_context, requirements_by_stage={stage: requirements_for_stage(project, stage) for stage in ("m3", "m4")})

    def approve_parameter(self, candidate: ParameterRecord, *, reviewer: str) -> "ProjectState":
        """Return updated state; persistence remains an explicit caller action."""
        if candidate.review_status not in {"validated", "approved"}:
            raise ValueError("only validated parameter candidates can be approved")
        approved = candidate.model_copy(update={"review_status": "approved", "approved_by": reviewer, "validation_flags": [*candidate.validation_flags, f"approved_by:{reviewer}"]})
        return self.model_copy(update={"approved_parameters": [*self.approved_parameters, approved]})
