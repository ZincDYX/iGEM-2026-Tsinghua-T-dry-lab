"""Approved construct knowledge, kept distinct from raw literature evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ConstructRecord(BaseModel):
    construct_id: str
    construct_type: str
    proteins: list[str] = Field(default_factory=list)
    sequences: dict[str, str] = Field(default_factory=dict)
    host: str | None = None
    scaffold: str | None = None
    idr: str | None = None
    recruitment_domains: list[str] = Field(default_factory=list)
    ligand_tags: list[str] = Field(default_factory=list)
    fusion_orientation: str | None = None
    domain_order: list[str] = Field(default_factory=list)
    linker_sequences: dict[str, str] = Field(default_factory=dict)
    promoter: str | None = None
    copy_number: str | None = None
    experimental_conditions: dict[str, str | float] = Field(default_factory=dict)
    measured_outputs: dict[str, float | str] = Field(default_factory=dict)
    source_type: str
    doi: str | None = None
    evidence: str | None = None
    review_status: str = "extracted"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    supersedes: str | None = None
    notes: str = ""

    def candidate_definition(self) -> dict[str, object]:
        return {"id": self.construct_id, "components": self.proteins + list(self.linker_sequences), "domain_order": self.domain_order, "fusion_orientation": self.fusion_orientation, "linker_ids": list(self.linker_sequences), "scaffold_id": self.scaffold, "recruitment_tags": self.ligand_tags, "enzyme_ids": [item for item in self.proteins if item in {"PT", "OC", "DMT"}], "provenance": {"source_type": self.source_type, "doi": self.doi, "record_id": self.construct_id}}


class ConstructRegistry:
    def __init__(self, records: list[ConstructRecord] | None = None) -> None: self._records = list(records or [])
    def add(self, record: ConstructRecord) -> None:
        if any(item.construct_id == record.construct_id for item in self._records): raise ValueError(f"duplicate construct_id: {record.construct_id}")
        self._records.append(record)
    def query(self, *, scaffold: str | None = None, host: str | None = None, approved_only: bool = True) -> list[ConstructRecord]:
        return [item for item in self._records if (not approved_only or item.review_status == "approved") and (scaffold is None or item.scaffold == scaffold) and (host is None or item.host == host)]
    def candidates(self) -> list[dict[str, object]]: return [item.candidate_definition() for item in self.query()]
    def records(self) -> list[ConstructRecord]: return list(self._records)
