from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from typing import Literal


class WetLabResult(BaseModel):
    experiment_id: str
    construct_id: str
    condition_id: str
    replicate_id: str
    timestamp: datetime | None = None
    protein_abundance: dict[str, float] = Field(default_factory=dict)
    imaging: dict[str, float] = Field(default_factory=dict)
    enzyme_activity: dict[str, float] = Field(default_factory=dict)
    metabolite_time: list[float] = Field(default_factory=list)
    metabolite_time_unit: Literal["h", "min", "s"] = "h"
    metabolites: dict[str, list[float]] = Field(default_factory=dict)
    biological_replicate_count: int = Field(default=1, ge=1)
    technical_replicate_count: int = Field(default=1, ge=1)
    batch_id: str | None = None
    control_available: bool = False
    notes: str = ""

    def time_hours(self) -> list[float]:
        divisor = {"h": 1.0, "min": 60.0, "s": 3600.0}[self.metabolite_time_unit]
        return [time / divisor for time in self.metabolite_time]


def load_wetlab_results(path: Path) -> list[WetLabResult]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("records", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("wet-lab JSON must be a list or {'records': [...]}")
    return [WetLabResult.model_validate(row) for row in rows]
