"""Serializable project state shared by workflow and agent modes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constructs import ConstructRecord
from .parameters import ParameterRecord, ParameterRegistry, m3_requirements, m4_requirements


class ProjectState(BaseModel):
    project_id: str
    constructs: list[ConstructRecord] = Field(default_factory=list)
    approved_parameters: list[ParameterRecord] = Field(default_factory=list)
    available_artifacts: list[str] = Field(default_factory=list)
    completed_stages: list[str] = Field(default_factory=list)
    pending_measurements: list[str] = Field(default_factory=list)
    wetlab_results: list[str] = Field(default_factory=list)
    hypotheses: list[dict[str, object]] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    def missing_inputs(self, stage: str, *, allow_assumptions: bool = False) -> list[str]:
        requirements = m3_requirements() if stage == "m3" else m4_requirements() if stage == "m4" else []
        registry = ParameterRegistry(self.approved_parameters)
        return [item.name for item in requirements if registry.resolve_for_model(item.name, allow_assumptions=allow_assumptions).status != "resolved"]
