from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractionSchema:
    schema_id: str
    domain: str
    instructions: tuple[str, ...]
    metrics: tuple[str, ...]
    raw: dict[str, Any]


def load_schema(path: Path) -> ExtractionSchema:
    raw = json.loads(path.read_text(encoding="utf-8"))
    metrics = tuple(metric["name"] for metric in raw.get("metrics", []) if "name" in metric)
    instructions = tuple(raw.get("prompt", {}).get("instructions", []))
    if not metrics:
        raise ValueError(f"Schema contains no metric names: {path}")
    return ExtractionSchema(
        schema_id=str(raw.get("schema_id", path.stem)),
        domain=str(raw.get("domain", "")),
        instructions=tuple(str(item) for item in instructions),
        metrics=metrics,
        raw=raw,
    )
