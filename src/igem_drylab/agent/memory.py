from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


MemoryKind = Literal["task", "tool_call", "artifact", "parameter", "wet_lab", "failure", "reflection", "note"]


class MemoryRecord(BaseModel):
    record_id: str
    kind: MemoryKind = "note"
    content: str
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMemory:
    """Typed durable memory with transparent lexical retrieval.

    A local lexical ranker is intentional: it is reproducible and requires no
    embedding API. It is not presented as semantic retrieval. Replace it with a
    versioned embedding index only when a real evaluation set justifies that
    extra dependency.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any] | MemoryRecord) -> MemoryRecord:
        typed = record if isinstance(record, MemoryRecord) else self._coerce(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(typed.model_dump_json() + "\n")
        return typed

    def load_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [record.model_dump(mode="json") for record in self.records()[-limit:]]

    def records(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        rows: list[MemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(MemoryRecord.model_validate_json(line))
            except ValueError:
                continue
        return rows

    def search(self, query: str, *, limit: int = 8, kinds: set[MemoryKind] | None = None) -> list[MemoryRecord]:
        tokens = set(_tokens(query))
        ranked: list[tuple[float, MemoryRecord]] = []
        for record in self.records():
            if kinds and record.kind not in kinds:
                continue
            haystack = set(_tokens(" ".join([record.content, *record.tags, record.source or ""])))
            overlap = len(tokens & haystack)
            if overlap:
                ranked.append((overlap / max(1, len(tokens)), record))
        ranked.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [record for _score, record in ranked[:limit]]

    def _coerce(self, raw: dict[str, Any]) -> MemoryRecord:
        event = str(raw.get("event", "note"))
        kind: MemoryKind = "failure" if "fail" in event else "note"
        if "task" in event:
            kind = "task"
        if "tool" in event:
            kind = "tool_call"
        return MemoryRecord(record_id=f"{event}-{datetime.now(timezone.utc).timestamp():.6f}", kind=kind, content=event, metadata=raw)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())
