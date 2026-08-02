from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ArtifactRecord(BaseModel):
    artifact_id: str
    path: Path
    kind: str
    producer_step_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactStore:
    """Track produced files and provenance.

    TODO: add checksums, schema validation, immutable run directories, and
    lineage queries such as "which tool produced this CSV?".
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.records: dict[str, ArtifactRecord] = {}

    def register(self, record: ArtifactRecord) -> None:
        self.records[record.artifact_id] = record

    def get(self, artifact_id: str) -> ArtifactRecord | None:
        return self.records.get(artifact_id)
