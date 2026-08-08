"""Parameter registry models.

Literature extraction yields evidence, not automatically validated parameters.
Only records explicitly entered into this registry may be supplied to M3/M4 in
``execution.mode=real``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ParameterSourceType = Literal["literature", "wetlab", "prediction", "assumption"]


class ParameterValidationError(ValueError):
    """A parameter lacks the provenance required for scientific computation."""


class ParameterRecord(BaseModel):
    parameter_id: str
    name: str
    value: float
    unit: str
    source_type: ParameterSourceType
    source_reference: str
    doi: str | None = None
    condition: str | None = None
    uncertainty: float | None = Field(default=None, ge=0)
    uncertainty_type: str | None = None
    measured_at: datetime | None = None
    model_version: str | None = None
    review_status: Literal["unreviewed", "reviewed", "rejected"] = "unreviewed"
    notes: str = ""

    @model_validator(mode="after")
    def _validate_source(self) -> "ParameterRecord":
        if not self.source_reference.strip():
            raise ValueError("source_reference is required")
        if self.source_type == "literature" and not self.doi:
            raise ValueError("literature parameters require a DOI")
        if self.uncertainty is not None and not self.uncertainty_type:
            raise ValueError("uncertainty_type is required when uncertainty is provided")
        return self


def validate_parameters(
    records: list[ParameterRecord], *, required_names: set[str], allow_assumptions: bool = False
) -> tuple[dict[str, ParameterRecord], list[str]]:
    """Return reviewed parameters and missing/invalid names without inferring values."""
    selected = {record.name: record for record in records if record.review_status == "reviewed"}
    missing: list[str] = []
    for name in sorted(required_names):
        record = selected.get(name)
        if record is None:
            missing.append(name)
        elif record.source_type == "assumption" and not allow_assumptions:
            missing.append(f"{name} (assumption not allowed)")
    return selected, missing
