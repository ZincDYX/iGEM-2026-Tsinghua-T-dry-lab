from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AgentMemory:
    """Minimal durable memory interface.

    TODO: replace this JSONL store with a typed experiment memory containing
    datasets, parameter provenance, failed tool attempts, wet-lab feedback, and
    retrieval policies. Do not store API keys or private full text here.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-limit:]
