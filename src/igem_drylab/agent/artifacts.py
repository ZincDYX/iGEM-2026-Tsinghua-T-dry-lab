from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ArtifactRecord(BaseModel):
    artifact_id: str
    path: Path
    kind: str
    producer_step_id: str | None = None
    parent_artifact_ids: list[str] = Field(default_factory=list)
    sha256: str | None = None
    size_bytes: int | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactStore:
    """Durable artifact manifest with integrity and lineage checks."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "artifact_manifest.json"
        self.records = self._load()

    def register(self, record: ArtifactRecord, *, require_exists: bool = False) -> ArtifactRecord:
        path = Path(record.path)
        if require_exists and not path.exists():
            raise FileNotFoundError(f"Artifact does not exist: {path}")
        if path.exists() and path.is_file():
            record = record.model_copy(update={"path": path, "sha256": _sha256(path), "size_bytes": path.stat().st_size})
        self.records[record.artifact_id] = record
        self._persist()
        return record

    def get(self, artifact_id: str) -> ArtifactRecord | None:
        return self.records.get(artifact_id)

    def verify(self, artifact_id: str) -> tuple[bool, str]:
        record = self.records.get(artifact_id)
        if record is None:
            return False, "artifact_not_registered"
        if not record.path.exists():
            return False, "artifact_missing"
        if record.sha256 and record.path.is_file() and _sha256(record.path) != record.sha256:
            return False, "artifact_checksum_mismatch"
        return True, "artifact_verified"

    def lineage(self, artifact_id: str) -> list[ArtifactRecord]:
        seen: set[str] = set()
        ordered: list[ArtifactRecord] = []

        def visit(current: str) -> None:
            if current in seen or current not in self.records:
                return
            seen.add(current)
            record = self.records[current]
            for parent in record.parent_artifact_ids:
                visit(parent)
            ordered.append(record)

        visit(artifact_id)
        return ordered

    def summaries(self, limit: int = 20) -> list[dict[str, Any]]:
        records = list(self.records.values())[-limit:]
        return [{"artifact_id": item.artifact_id, "kind": item.kind, "path": str(item.path), "producer": item.producer_step_id} for item in records]

    def _load(self) -> dict[str, ArtifactRecord]:
        if not self.manifest_path.exists():
            return {}
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {item["artifact_id"]: ArtifactRecord.model_validate(item) for item in payload.get("records", [])}

    def _persist(self) -> None:
        payload = {"records": [record.model_dump(mode="json") for record in self.records.values()]}
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.manifest_path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
