"""Serializable project state shared by workflow and agent modes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constructs import ConstructRecord
from .parameters import ParameterRecord, ParameterRegistry, m3_requirements, m4_requirements, resolve_requirement
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

    def missing_inputs(self, stage: str, *, allow_assumptions: bool = False, construct_id: str | None = None, condition_id: str | None = None, enable_degradation: bool = False) -> list[str]:
        requirements = m3_requirements() if stage == "m3" else m4_requirements(include_degradation=enable_degradation) if stage == "m4" else []
        registry = ParameterRegistry(self.approved_parameters)
        return [item.name for item in requirements if resolve_requirement(registry, item, self.experimental_context, allow_assumptions=allow_assumptions, construct_id=construct_id, condition_id=condition_id).status != "resolved"]

    def approve_parameter(self, candidate: ParameterRecord, *, reviewer: str) -> "ProjectState":
        """Return updated state; persistence remains an explicit caller action."""
        if candidate.review_status not in {"validated", "approved"}:
            raise ValueError("only validated parameter candidates can be approved")
        approved = candidate.model_copy(update={"review_status": "approved", "approved_by": reviewer, "validation_flags": [*candidate.validation_flags, f"approved_by:{reviewer}"]})
        return self.model_copy(update={"approved_parameters": [*self.approved_parameters, approved]})
