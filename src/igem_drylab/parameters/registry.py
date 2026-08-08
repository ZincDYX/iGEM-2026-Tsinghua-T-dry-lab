"""Small file-friendly registry with explicit conflict and lineage behaviour."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .models import ParameterRecord


class ParameterResolution(BaseModel):
    status: str
    selected_parameter: ParameterRecord | None = None
    alternatives: list[ParameterRecord] = []
    reasons: list[str] = []


class ParameterRegistry:
    def __init__(self, records: list[ParameterRecord] | None = None) -> None: self._records = list(records or [])
    def add(self, record: ParameterRecord) -> None:
        if any(item.parameter_id == record.parameter_id for item in self._records): raise ValueError(f"duplicate parameter_id: {record.parameter_id}")
        self._records.append(record)
    def get(self, parameter_id: str) -> ParameterRecord | None: return next((item for item in self._records if item.parameter_id == parameter_id), None)
    def query(self, *, name: str | None = None, parameter_type: str | None = None, enzyme_id: str | None = None, substrate_id: str | None = None) -> list[ParameterRecord]:
        return [item for item in self._records if (name is None or item.name == name) and (parameter_type is None or item.parameter_type == parameter_type) and (enzyme_id is None or item.enzyme_id == enzyme_id) and (substrate_id is None or item.substrate_id == substrate_id)]
    def resolve_for_model(self, name: str, *, allow_assumptions: bool = False) -> ParameterResolution:
        candidates = [item for item in self.query(name=name) if item.review_status == "approved" and (allow_assumptions or item.source_type != "assumption")]
        if not candidates: return ParameterResolution(status="missing", reasons=["no_approved_compatible_parameter"])
        ranked = sorted(candidates, key=lambda item: ({"wetlab": 0, "literature": 1, "prediction": 2, "assumption": 3}[item.source_type], -item.parameter_version, item.parameter_id))
        best = ranked[0]; tied = [item for item in ranked if item.source_type == best.source_type and item.parameter_version == best.parameter_version]
        if len({str(item.value) + str(item.unit) for item in tied}) > 1: return ParameterResolution(status="conflict", alternatives=tied, reasons=["conflicting_equally_ranked_records"])
        return ParameterResolution(status="resolved", selected_parameter=best, alternatives=ranked[1:], reasons=["selected_by_explicit_source_priority_and_version"])
    def list_conflicts(self) -> list[ParameterResolution]:
        return [self.resolve_for_model(name) for name in sorted({item.name for item in self._records}) if self.resolve_for_model(name).status == "conflict"]
    def provenance(self, parameter_id: str) -> list[ParameterRecord]:
        current = self.get(parameter_id); lineage: list[ParameterRecord] = []
        while current is not None:
            lineage.append(current); current = self.get(current.supersedes) if current.supersedes else None
        return lineage
    def records(self) -> list[ParameterRecord]: return list(self._records)
    @classmethod
    def from_jsonl(cls, path: Path) -> "ParameterRegistry": return cls([ParameterRecord.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
    def to_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(item.model_dump_json() for item in self._records) + "\n", encoding="utf-8")


def validate_parameters(records: list[ParameterRecord], *, required_names: set[str], allow_assumptions: bool = False) -> tuple[dict[str, ParameterRecord], list[str]]:
    """Compatibility helper returning only resolved, approved numeric records."""
    registry = ParameterRegistry(records); selected: dict[str, ParameterRecord] = {}; missing: list[str] = []
    for name in sorted(required_names):
        resolution = registry.resolve_for_model(name, allow_assumptions=allow_assumptions)
        if resolution.status == "resolved" and resolution.selected_parameter is not None:
            selected[name] = resolution.selected_parameter
        else:
            missing.append(f"{name} ({resolution.status})")
    return selected, missing
