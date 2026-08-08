"""Reviewed scientific parameter records, separate from raw literature evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ParameterSourceType = Literal["literature", "wetlab", "prediction", "assumption"]
ParameterType = Literal["kcat", "km", "kd", "kp", "phi", "abundance", "activity_ratio", "degradation_rate", "export_rate", "hill_coefficient", "other"]
ReviewStatus = Literal["extracted", "validated", "approved", "rejected"]


class ParameterValidationError(ValueError):
    pass


class ParameterUncertainty(BaseModel):
    value: float | None = Field(default=None, ge=0)
    lower: float | None = None
    upper: float | None = None
    type: str | None = None


class ParameterRecord(BaseModel):
    parameter_id: str
    name: str
    value: float | str
    unit: str | None = None
    species_id: str | None = None
    enzyme_id: str | None = None
    substrate_id: str | None = None
    product_id: str | None = None
    parameter_type: ParameterType = "other"
    source_type: ParameterSourceType
    source_reference: str | None = None
    doi: str | None = None
    evidence_text: str | None = None
    evidence_location: str | None = None
    conditions: dict[str, str | float] = Field(default_factory=dict)
    uncertainty: ParameterUncertainty | None = None
    review_status: ReviewStatus = "extracted"
    validation_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str | None = None
    parameter_version: int = Field(default=1, ge=1)
    supersedes: str | None = None
    derived_from: list[str] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def _validate_provenance(self) -> "ParameterRecord":
        if self.source_type == "literature" and not self.doi:
            raise ValueError("literature parameter records require a DOI")
        if self.source_type == "literature" and self.review_status == "approved" and not self.evidence_text:
            raise ValueError("approved literature parameters require evidence_text")
        if isinstance(self.value, (int, float)) and self.unit is None:
            raise ValueError("numeric parameter values require an explicit unit")
        return self

    @property
    def numeric_value(self) -> float:
        if not isinstance(self.value, (int, float)):
            raise ParameterValidationError(f"Parameter '{self.parameter_id}' has a non-numeric value")
        return float(self.value)
