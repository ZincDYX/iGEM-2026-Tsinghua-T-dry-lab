"""File-friendly reviewed registry with explicit compatibility and conflicts."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .dimensions import validate_requirement_value
from .models import ParameterRecord
from .requirements import ParameterRequirement
from .validation import condition_compatibility, identity_compatibility


def resolve_requirement(registry: "ParameterRegistry", requirement: ParameterRequirement, context: object, *, allow_assumptions: bool, construct_id: str | None = None, condition_id: str | None = None, require_provenance: bool = False) -> ParameterResolution:
    """Shared production resolution entry point for pipeline, MCP, and agent."""
    return registry.resolve(requirement, host=getattr(context, "host", None), strain=getattr(context, "strain", None), assay_system=getattr(context, "assay_system", None), pH=getattr(context, "pH", None), temperature_c=getattr(context, "temperature_c", None), allow_assumptions=allow_assumptions, construct_id=construct_id, condition_id=condition_id, require_provenance=require_provenance)


class ParameterResolution(BaseModel):
    status: str
    selected_parameter: ParameterRecord | None = None
    canonical_value: float | None = None
    alternatives: list[ParameterRecord] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class ParameterRegistry:
    def __init__(self, records: list[ParameterRecord] | None = None) -> None:
        self._records = list(records or [])
        identifiers = [record.parameter_id for record in self._records]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate_parameter_id")
        for record in self._records:
            if record.supersedes == record.parameter_id:
                raise ValueError("self_supersedes")
            if record.supersedes and self.get(record.supersedes) is None:
                raise ValueError("dangling_supersedes")
            if record.supersedes:
                parent = self.get(record.supersedes)
                if parent and not _lineage_compatible(record, parent):
                    raise ValueError("incompatible_supersedes")
        for record in self._records:
            seen: set[str] = set(); current = record
            while current.supersedes:
                if current.parameter_id in seen:
                    raise ValueError("supersedes_cycle")
                seen.add(current.parameter_id)
                current = self.get(current.supersedes)  # validated above

    def add(self, record: ParameterRecord) -> None:
        if self.get(record.parameter_id):
            raise ValueError(f"duplicate parameter_id: {record.parameter_id}")
        self._records.append(record)
        try:
            ParameterRegistry(self._records)
        except Exception:
            self._records.pop()
            raise

    def get(self, parameter_id: str) -> ParameterRecord | None:
        return next((item for item in self._records if item.parameter_id == parameter_id), None)

    def query(self, **filters: str | None) -> list[ParameterRecord]:
        return [item for item in self._records if all(value is None or getattr(item, key) == value for key, value in filters.items())]

    def resolve(self, requirement: ParameterRequirement, *, host: str | None = None, strain: str | None = None, assay_system: str | None = None, pH: float | None = None, temperature_c: float | None = None, mutant_allowed: bool = False, allow_assumptions: bool = False, construct_id: str | None = None, condition_id: str | None = None, require_provenance: bool = False) -> ParameterResolution:
        candidates = [item for item in self.query(name=requirement.name) if item.review_status == "approved" and (allow_assumptions or item.source_type != "assumption")]
        compatible: list[tuple[ParameterRecord, float]] = []
        rejected: list[str] = []
        for record in candidates:
            if require_provenance and (not has_required_provenance(record) or not record.approved_by):
                rejected.append("incomplete_required_provenance")
                continue
            if record.parameter_type != requirement.parameter_type:
                rejected.append("parameter_type_mismatch")
                continue
            if record.construct_id is not None and record.construct_id != construct_id:
                rejected.append("construct_scope_mismatch")
                continue
            if record.condition_id is not None and record.condition_id != condition_id:
                rejected.append("condition_scope_mismatch")
                continue
            if requirement.species_id and record.species_id != requirement.species_id and (require_provenance or record.species_id is not None):
                rejected.append("species_mismatch")
                continue
            if requirement.phase and record.conditions.get("phase") != requirement.phase and (require_provenance or record.conditions.get("phase") is not None):
                rejected.append("phase_mismatch")
                continue
            identity = identity_compatibility(record, enzyme_id=requirement.enzyme_id, substrate_id=requirement.substrate_id, product_id=requirement.product_id, host=host, mutant_allowed=mutant_allowed)
            condition = condition_compatibility(record, host=host, strain=strain, assay_system=assay_system, pH=pH, temperature_c=temperature_c)
            if identity.level == "incompatible" or condition.level == "incompatible":
                rejected.extend(identity.reasons + condition.reasons)
                continue
            if identity.level == "weak" or condition.level == "weak":
                rejected.extend(("weak_match", *identity.reasons, *condition.reasons))
                continue
            try:
                value = validate_requirement_value(record.numeric_value, record.unit, requirement)
            except ValueError as error:
                rejected.append(str(error))
                continue
            compatible.append((record, value))
        if not compatible:
            return ParameterResolution(status="unresolved", reasons=sorted(set(rejected or ["no_approved_exact_compatible_parameter"])))
        # Explicit replacements define the current lineage leaf before source
        # priority is considered.  This keeps resolve(), provenance(), and
        # conflict scans on one graph policy.
        compatible = [
            pair for pair in compatible
            if not any(self._supersedes_transitively(other[0], pair[0]) for other in compatible if other[0].parameter_id != pair[0].parameter_id)
        ]
        def scope_rank(record: ParameterRecord) -> int:
            if record.construct_id == construct_id and record.condition_id == condition_id and construct_id is not None and condition_id is not None: return 0
            if record.construct_id == construct_id and record.condition_id is None and construct_id is not None: return 1
            if record.construct_id is None and record.condition_id == condition_id and condition_id is not None: return 2
            return 3
        # Version is deliberately not a replacement policy.  A newer number may
        # win only when its reviewed record explicitly supersedes the older one.
        ranked = sorted(compatible, key=lambda pair: (scope_rank(pair[0]), evidence_priority(pair[0]), pair[0].parameter_id))
        best, value = ranked[0]
        tied = [pair for pair in ranked if scope_rank(pair[0]) == scope_rank(best) and evidence_priority(pair[0]) == evidence_priority(best)]
        if len(tied) > 1 and len({round(pair[1], 12) for pair in tied}) > 1:
            replacement = [pair for pair in tied if all(self._supersedes_transitively(pair[0], other[0]) or pair[0].parameter_id == other[0].parameter_id for other in tied)]
            if len(replacement) == 1:
                best, value = replacement[0]
            else:
                return ParameterResolution(status="conflict", alternatives=[pair[0] for pair in tied], reasons=["conflicting_equally_ranked_records_without_explicit_supersedes"])
        return ParameterResolution(status="resolved", selected_parameter=best, canonical_value=value, alternatives=[pair[0] for pair in ranked[1:]], reasons=["approved_exact_identity_condition_dimension_and_scope_match"])

    def resolve_for_model(self, name: str, *, allow_assumptions: bool = False) -> ParameterResolution:
        """Legacy name-only inspection API; scientific stages must call ``resolve``."""
        candidates = [item for item in self.query(name=name) if item.review_status == "approved" and (allow_assumptions or item.source_type != "assumption")]
        if not candidates:
            return ParameterResolution(status="missing", reasons=["no_approved_parameter"])
        ranked = sorted(candidates, key=lambda item: ({"wetlab": 0, "literature": 1, "prediction": 2, "assumption": 3}[item.source_type], -item.parameter_version, item.parameter_id))
        best = ranked[0]
        tied = [item for item in ranked if item.source_type == best.source_type and item.parameter_version == best.parameter_version]
        if len({(str(item.value), item.unit) for item in tied}) > 1:
            return ParameterResolution(status="conflict", alternatives=tied, reasons=["conflicting_equally_ranked_records"])
        return ParameterResolution(status="resolved", selected_parameter=best, alternatives=ranked[1:], reasons=["legacy_name_only_resolution_not_for_scientific_stages"])

    def provenance(self, parameter_id: str) -> list[ParameterRecord]:
        lineage, current = [], self.get(parameter_id)
        while current:
            lineage.append(current)
            current = self.get(current.supersedes) if current.supersedes else None
        return lineage

    def _supersedes_transitively(self, child: ParameterRecord, ancestor: ParameterRecord) -> bool:
        return ancestor.parameter_id in {item.parameter_id for item in self.provenance(child.parameter_id)[1:]}

    def records(self) -> list[ParameterRecord]: return list(self._records)
    def list_conflicts(self) -> list[ParameterRecord]:
        """Return incompatible same-tier *leaves* using the resolver lineage policy."""
        groups: dict[tuple[object, ...], list[ParameterRecord]] = {}
        for record in self._records:
            if record.review_status != "approved":
                continue
            key = (
                record.name, record.parameter_type, record.enzyme_id, record.substrate_id,
                record.product_id, record.species_id, record.conditions.get("phase"),
                record.construct_id, record.condition_id, evidence_priority(record),
            )
            groups.setdefault(key, []).append(record)
        conflicts: list[ParameterRecord] = []
        for peers in groups.values():
            leaves = [item for item in peers if not any(self._supersedes_transitively(other, item) for other in peers if other.parameter_id != item.parameter_id)]
            if len(leaves) < 2:
                continue
            requirement = _known_requirement(leaves[0].name)
            values = {round(validate_requirement_value(item.numeric_value, item.unit, requirement), 12) for item in leaves}
            if len(values) > 1:
                conflicts.extend(leaves)
        return conflicts
    @classmethod
    def from_jsonl(cls, path: Path) -> "ParameterRegistry": return cls([ParameterRecord.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
    def to_jsonl(self, path: Path) -> None: path.write_text("\n".join(item.model_dump_json() for item in self._records) + "\n", encoding="utf-8")


def evidence_priority(record: ParameterRecord) -> int:
    """Central production evidence policy; lower is stronger and ties conflict."""
    if record.source_type == "wetlab":
        return 0 if record.derivation_type == "direct_measurement" else 1
    if record.source_type == "literature":
        return 2 if record.derivation_type != "literature_extraction" else 3
    return 4 if record.source_type == "prediction" else 5


def _lineage_compatible(child: ParameterRecord, parent: ParameterRecord) -> bool:
    """A replacement may update a value, never silently change its scientific identity."""
    fields = (
        "name", "parameter_type", "enzyme_id", "substrate_id", "product_id",
        "species_id", "construct_id", "condition_id",
    )
    # Legacy records may be sparse.  They remain queryable through the legacy
    # API, while strict production approval requires the complete identity.
    if any(
        getattr(child, field) is not None
        and getattr(parent, field) is not None
        and getattr(child, field) != getattr(parent, field)
        for field in fields
    ):
        return False
    child_phase, parent_phase = child.conditions.get("phase"), parent.conditions.get("phase")
    return child_phase is None or parent_phase is None or child_phase == parent_phase


def _known_requirement(name: str) -> ParameterRequirement:
    """Conflict scanning does not invent dimensions from a unit string."""
    from .requirements import m3_requirements, m4_requirements
    requirement = next(
        (item for item in [*m3_requirements(), *m4_requirements(include_degradation=True)] if item.name == name),
        None,
    )
    if requirement is None:
        raise ValueError(f"unknown_parameter_requirement_for_conflict_scan:{name}")
    return requirement


def has_required_provenance(record: ParameterRecord) -> bool:
    if record.source_type == "literature":
        return bool(record.doi and record.evidence_text)
    if record.source_type == "wetlab":
        if not record.source_reference:
            return False
        return bool(record.derived_from) if record.derivation_type == "model_fit" else True
    return record.source_type in {"prediction", "assumption"} and bool(record.source_reference)


def validate_parameters(records: list[ParameterRecord], *, requirements: list[ParameterRequirement] | None = None, required_names: set[str] | None = None, allow_assumptions: bool = False, host: str | None = None, strain: str | None = None, assay_system: str | None = None, pH: float | None = None, temperature_c: float | None = None, construct_id: str | None = None, condition_id: str | None = None, require_provenance: bool = False) -> tuple[dict[str, ParameterResolution], list[str]]:
    legacy = requirements is None
    if requirements is None:
        requirements = [ParameterRequirement(name=name, parameter_type="other", dimension="dimensionless") for name in sorted(required_names or set())]
    registry = ParameterRegistry(records)
    resolutions = {item.name: (registry.resolve_for_model(item.name, allow_assumptions=allow_assumptions) if legacy else registry.resolve(item, host=host, strain=strain, assay_system=assay_system, pH=pH, temperature_c=temperature_c, allow_assumptions=allow_assumptions, construct_id=construct_id, condition_id=condition_id, require_provenance=require_provenance)) for item in requirements}
    if legacy:
        selected = {name: result.selected_parameter for name, result in resolutions.items() if result.selected_parameter is not None}
        return selected, [f"{name} ({result.status})" for name, result in resolutions.items() if result.status != "resolved"]  # type: ignore[return-value]
    return resolutions, [f"{name} ({result.status}: {','.join(result.reasons)})" for name, result in resolutions.items() if result.status != "resolved"]
