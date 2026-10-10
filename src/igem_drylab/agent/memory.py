from __future__ import annotations

import json
import re
from heapq import nlargest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


MemoryKind = Literal["task", "tool_call", "artifact", "parameter", "wet_lab", "failure", "reflection", "note"]


class ScientificClaim(BaseModel):
    """A comparable assertion; events and revised outputs are not claims.

    Values must already use the declared canonical unit/entity basis. Different
    conditions or methods are deliberately different comparison scopes.
    """
    subject_ref: str
    quantity: str
    construct_ref: str
    condition_ref: str
    model_version: str
    canonical_unit: str
    entity_basis: str
    value: str | float | bool
    supersedes_record_id: str | None = None


class MemoryRecord(BaseModel):
    record_id: str
    kind: MemoryKind = "note"
    content: str
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)
    claim: ScientificClaim | None = None


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
        if limit <= 0 or not self.path.exists(): return []
        rows = []
        # Read only enough tail blocks for the requested valid JSONL records.
        with self.path.open("rb") as handle:
            handle.seek(0,2)
            position,pending = handle.tell(),b""
            while position and len(rows) < limit:
                start = max(0,position-65536)
                handle.seek(start)
                lines = (handle.read(position-start)+pending).split(b"\n")
                position = start
                pending = lines[0] if position else b""
                for line in reversed(lines[1:] if position else lines):
                    if not line.strip(): continue
                    try: rows.append(MemoryRecord.model_validate_json(line).model_dump(mode="json"))
                    except ValueError: continue
                    if len(rows) == limit: break
        return rows[::-1]

    def records(self) -> list[MemoryRecord]:
        return list(self._iter_records())

    def _iter_records(self):
        if not self.path.exists():
            return
        with self.path.open("r",encoding="utf-8") as handle:
            for line in handle:
                if not line.strip(): continue
                try: yield MemoryRecord.model_validate_json(line)
                except ValueError: continue

    def search(self, query: str, *, limit: int = 8, kinds: set[MemoryKind] | None = None) -> list[MemoryRecord]:
        tokens = set(_tokens(query))
        if limit <= 0: return []
        def ranked():
            for record in self._iter_records():
                if kinds and record.kind not in kinds: continue
                haystack = set(_tokens(" ".join([record.content,*record.tags,record.source or ""])))
                overlap = len(tokens & haystack)
                if overlap: yield overlap / max(1,len(tokens)),record
        # Exact old lexical ordering, O(limit) retained records, no approximation.
        return [record for _,record in nlargest(limit,ranked(),key=lambda item:(item[0],item[1].created_at))]

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
