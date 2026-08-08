"""Explicit scientific hypotheses; no fabricated numeric confidence values."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HypothesisRecord(BaseModel):
    hypothesis_id: str
    statement: str
    status: str = "tentative"
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    required_measurements: list[str] = Field(default_factory=list)
