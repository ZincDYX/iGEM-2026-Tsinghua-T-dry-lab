"""Explicit, review-gated conversion of wet-lab measurements to parameters."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pathlib import Path
import yaml

from igem_drylab.parameters import ParameterRecord

from .models import WetLabResult
from .qc import QcReport


class MeasurementMapping(BaseModel):
    """Human-declared mapping; the software never infers biology from a column."""

    parameter_id: str
    name: str
    source_field: str
    unit: str
    parameter_type: str = "other"
    enzyme_id: str | None = None
    substrate_id: str | None = None
    product_id: str | None = None
    supersedes: str | None = None
    conditions: dict[str, str | float] = Field(default_factory=dict)
    review_status: str = "validated"


def parameter_updates_from_measurements(
    results: list[WetLabResult], qc_reports: list[QcReport], mappings: list[MeasurementMapping]
) -> list[ParameterRecord]:
    """Make validated wet-lab candidates from explicit scalar fields only.

    The output is intentionally *not approved*. A scientific reviewer must
    decide whether the measured quantity is a usable model parameter.
    """
    qc_by_experiment = {report.experiment_id: report for report in qc_reports}
    updates: list[ParameterRecord] = []
    for result in results:
        report = qc_by_experiment.get(result.experiment_id)
        if report is None or not report.passed:
            continue
        for mapping in mappings:
            value = _scalar_field(result, mapping.source_field)
            if value is None:
                continue
            updates.append(ParameterRecord(
                parameter_id=f"{mapping.parameter_id}:{result.experiment_id}:{result.replicate_id}",
                name=mapping.name, value=value, unit=mapping.unit,
                parameter_type=mapping.parameter_type, source_type="wetlab",
                derivation_type="direct_measurement", source_reference=result.experiment_id, conditions=mapping.conditions,
                enzyme_id=mapping.enzyme_id, substrate_id=mapping.substrate_id,
                product_id=mapping.product_id, review_status="validated",
                construct_id=result.construct_id, condition_id=result.condition_id,
                supersedes=mapping.supersedes,
                validation_flags=["requires_human_approval_before_model_use"],
                notes=f"Explicit mapping from wetlab field '{mapping.source_field}'.",
            ))
    return updates


def _scalar_field(result: WetLabResult, field: str) -> float | None:
    """Read a declared ``group.key`` scalar; arbitrary expressions are rejected."""
    group, separator, key = field.partition(".")
    if not separator or group not in {"protein_abundance", "imaging", "enzyme_activity"}:
        raise ValueError("source_field must be protein_abundance.*, imaging.*, or enzyme_activity.*")
    value = getattr(result, group).get(key)
    return float(value) if value is not None else None


def approve_and_persist_parameter(project_path: Path, candidate: ParameterRecord, *, reviewer: str) -> ParameterRecord:
    """Human-triggered YAML update retaining old records and provenance."""
    if candidate.review_status != "validated":
        raise ValueError("only validated candidates may be approved")
    raw = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    records = raw.setdefault("parameters", [])
    approved = candidate.model_copy(update={"review_status": "approved", "approved_by": reviewer, "validation_flags": [*candidate.validation_flags, f"approved_by:{reviewer}"]})
    records.append(approved.model_dump(mode="json"))
    project_path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return approved
