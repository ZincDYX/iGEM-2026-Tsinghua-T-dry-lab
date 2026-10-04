"""Explicit, review-gated conversion of wet-lab measurements to parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pathlib import Path
import yaml

from igem_drylab.parameters import ParameterRecord, ParameterRegistry
from igem_drylab.parameters.models import validate_provenance_combination
from igem_drylab.parameters.dimensions import validate_requirement_value
from igem_drylab.parameters.requirements import ParameterRequirement, requirements_for_stage

if TYPE_CHECKING:
    from igem_drylab.pipeline.config import ProjectConfig

from .models import WetLabResult
from .qc import QcReport


class MeasurementMapping(BaseModel):
    """Human-declared mapping; the software never infers biology from a column."""

    source_field: str
    target_stage: str
    target_requirement_name: str
    unit: str
    parameter_id_prefix: str = "wetlab"
    supersedes: str | None = None
    model_config = ConfigDict(extra="forbid")


def parameter_updates_from_measurements(
    project: "ProjectConfig", results: list[WetLabResult], qc_reports: list[QcReport], mappings: list[MeasurementMapping]
) -> list[ParameterRecord]:
    """Make validated wet-lab candidates from explicit scalar fields only.

    The output is intentionally *not approved*. A scientific reviewer must
    decide whether the measured quantity is a usable model parameter.
    """
    qc_by_experiment = {(report.experiment_id, report.replicate_id): report for report in qc_reports}
    updates: list[ParameterRecord] = []
    for result in results:
        report = qc_by_experiment.get((result.experiment_id, result.replicate_id))
        if report is None or not report.passed:
            continue
        for mapping in mappings:
            value = _scalar_field(result, mapping.source_field)
            if value is None:
                continue
            requirement = _requirement(project, mapping.target_stage, mapping.target_requirement_name)
            canonical = validate_requirement_value(value, mapping.unit, requirement)
            assay = result.conditions_for(mapping.source_field)
            measurement = result.partition_measurements.get(mapping.source_field.removeprefix("partition_measurements."))
            if mapping.source_field.startswith("partition_measurements.") and (
                    requirement.parameter_type != "kp" or mapping.unit != "1" or
                    requirement.species_id != mapping.source_field.split(".", 1)[1]):
                raise ValueError("partition_measurement_requires_matching_dimensionless_metabolite_Kp")
            updates.append(ParameterRecord(
                parameter_id=f"{mapping.parameter_id_prefix}:{mapping.target_requirement_name}:{result.experiment_id}:{result.replicate_id}",
                name=requirement.name, value=canonical, unit=requirement.canonical_unit,
                parameter_type=requirement.parameter_type, species_id=requirement.species_id, source_type="wetlab",
                derivation_type="direct_measurement", source_reference=f"{result.experiment_id}:{result.replicate_id}", conditions=assay.parameter_conditions() if assay else {},
                enzyme_id=requirement.enzyme_id, substrate_id=requirement.substrate_id,
                product_id=requirement.product_id, review_status="validated",
                construct_id=result.construct_id, condition_id=assay.condition_id if assay else result.condition_id,
                supersedes=mapping.supersedes,
                validation_flags=["requires_human_approval_before_model_use"] + ([] if assay else ["experimental_conditions_not_reported"]),
                derived_from=[measurement.raw_data_sha256, measurement.source_reference] if measurement else [],
                notes=f"Requirement-aware mapping from wetlab field '{mapping.source_field}'." +
                    (f" Calibration: {measurement.calibration_reference}; recovery: {measurement.recovery_reference}; phase volumes: {measurement.phase_volume_reference}." if measurement else ""),
            ))
    return updates


def _scalar_field(result: WetLabResult, field: str) -> float | None:
    """Read a declared ``group.key`` scalar; arbitrary expressions are rejected."""
    group, separator, key = field.partition(".")
    if separator and group == "partition_measurements":
        measurement = result.partition_measurements.get(key)
        return measurement.kp if measurement else None
    if not separator or group not in {"protein_abundance", "imaging", "enzyme_activity"}:
        raise ValueError("source_field must be protein_abundance.*, imaging.*, or enzyme_activity.*")
    value = getattr(result, group).get(key)
    return float(value) if value is not None else None


def _requirement(project: "ProjectConfig", stage: str, name: str) -> ParameterRequirement:
    requirement = next((item for item in requirements_for_stage(project, stage) if item.name == name), None)
    if requirement is None:
        raise ValueError("unknown_target_requirement")
    return requirement


def validate_candidate_against_registry(records: list[ParameterRecord], candidate: ParameterRecord, requirement: ParameterRequirement, reviewer: str, *, formal_context: object | None = None) -> None:
    """Validate the one approval boundary shared by state, CLI, MCP and YAML writes."""
    if not reviewer.strip() or candidate.review_status != "validated": raise ValueError("validated_candidate_and_reviewer_required")
    if candidate.name != requirement.name or candidate.parameter_type != requirement.parameter_type: raise ValueError("candidate_requirement_mismatch")
    if candidate.enzyme_id != requirement.enzyme_id or candidate.substrate_id != requirement.substrate_id or candidate.product_id != requirement.product_id or candidate.species_id != requirement.species_id: raise ValueError("candidate_identity_mismatch")
    if requirement.phase and candidate.conditions.get("phase") != requirement.phase: raise ValueError("candidate_phase_mismatch")
    validate_requirement_value(candidate.numeric_value, candidate.unit, requirement)
    validate_provenance_combination(candidate.source_type, candidate.derivation_type)
    if candidate.source_type == "wetlab" and not candidate.source_reference: raise ValueError("wetlab_source_required")
    if candidate.derivation_type == "model_fit" and not candidate.derived_from: raise ValueError("model_fit_lineage_required")
    ParameterRegistry([*records, candidate])
    if formal_context is not None:
        from igem_drylab.parameters import resolve_requirement
        approved = candidate.model_copy(update={"review_status": "approved", "approved_by": reviewer})
        # Applicability of this candidate, not an unrelated existing alternative.
        resolution = resolve_requirement(ParameterRegistry([approved.model_copy(update={"supersedes": None})]), requirement,
            formal_context, allow_assumptions=False, construct_id=candidate.construct_id,
            condition_id=candidate.condition_id, require_provenance=True)
        if resolution.status != "resolved":
            raise ValueError("candidate_not_formally_applicable:" + ",".join(resolution.reasons))


def validate_candidate_for_approval(project: "ProjectConfig", candidate: ParameterRecord, requirement: ParameterRequirement, reviewer: str) -> None:
    """Project-config convenience wrapper around the shared approval boundary."""
    formal = project.execution.mode == "real" and project.execution.analysis_grade == "formal_measured"
    from igem_drylab.pipeline.config import canonical_m4_condition_id
    target_condition = canonical_m4_condition_id(project.stages.m4_reaction)
    if formal and candidate.condition_id != target_condition:
        raise ValueError("candidate_target_condition_mismatch")
    validate_candidate_against_registry(project.parameters, candidate, requirement, reviewer,
        formal_context=project.experimental_context if formal else None)


def approve_and_persist_parameter(project_path: Path, candidate: ParameterRecord, *, reviewer: str, target_stage: str, target_requirement_name: str) -> ParameterRecord:
    """Human-triggered YAML update retaining old records and provenance."""
    from igem_drylab.pipeline.config import load_config
    project = load_config(project_path); raw = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    validate_candidate_for_approval(project, candidate, _requirement(project, target_stage, target_requirement_name), reviewer)
    records = raw.setdefault("parameters", [])
    approved = candidate.model_copy(update={"review_status": "approved", "approved_by": reviewer, "validation_flags": [*candidate.validation_flags, f"approved_by:{reviewer}"]})
    records.append(approved.model_dump(mode="json"))
    project_path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return approved
