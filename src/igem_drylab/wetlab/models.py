from __future__ import annotations

import json
import math
from hashlib import sha256
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class WetLabResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    metabolite_concentration_unit: str | None = None
    metabolite_uncertainty: dict[str, list[float]] = Field(default_factory=dict)
    metabolite_uncertainty_type: Literal["sd", "sem", "ci"] | None = None
    metabolite_lod: dict[str, float] = Field(default_factory=dict)
    metabolite_loq: dict[str, float] = Field(default_factory=dict)
    metabolites: dict[str, list[float]] = Field(default_factory=dict)
    biological_replicate_count: int = Field(default=1, ge=1)
    technical_replicate_count: int = Field(default=1, ge=1)
    batch_id: str | None = None
    control_available: bool = False
    observation_kind: Literal["time_course", "steady_state"] = "time_course"
    measurement_compartment: Literal["intracellular", "extracellular", "total_extract"] | None = None
    concentration_basis: Literal["cell_volume", "medium_volume", "extraction_volume"] | None = None
    extraction_volume_l: float | None = Field(default=None, gt=0)
    raw_data_sha256: str | None = None
    source_replicate_data: list[dict] = Field(default_factory=list)
    notes: str = ""

    def time_hours(self) -> list[float]:
        divisor = {"h": 1.0, "min": 60.0, "s": 3600.0}[self.metabolite_time_unit]
        return [time / divisor for time in self.metabolite_time]

    @property
    def record_key(self) -> tuple[str, str, str, str]:
        return self.experiment_id, self.construct_id, self.condition_id, self.replicate_id

    @model_validator(mode="after")
    def _validate_series(self) -> "WetLabResult":
        if not all(math.isfinite(value) for value in self.metabolite_time):
            raise ValueError("nonfinite_metabolite_time")
        if len(set(self.metabolite_time)) != len(self.metabolite_time) or any(right <= left for left, right in zip(self.metabolite_time, self.metabolite_time[1:])):
            raise ValueError("metabolite_time_must_be_strictly_increasing")
        for species, values in self.metabolites.items():
            if len(values) != len(self.metabolite_time):
                raise ValueError(f"metabolite_time_length_mismatch:{species}")
            if any(not math.isfinite(value) or value < 0 for value in values):
                raise ValueError(f"invalid_metabolite_value:{species}")
            uncertainty = self.metabolite_uncertainty.get(species)
            if uncertainty is not None:
                if self.metabolite_uncertainty_type is None:
                    raise ValueError("uncertainty_type_required")
                if len(uncertainty) != len(values) or any(not math.isfinite(value) or value < 0 for value in uncertainty):
                    raise ValueError(f"invalid_uncertainty:{species}")
            lod, loq = self.metabolite_lod.get(species), self.metabolite_loq.get(species)
            if lod is not None and (not math.isfinite(lod) or lod < 0): raise ValueError(f"invalid_lod:{species}")
            if loq is not None and (not math.isfinite(loq) or loq < 0): raise ValueError(f"invalid_loq:{species}")
            if lod is not None and loq is not None and lod > loq: raise ValueError(f"lod_gt_loq:{species}")
        return self


def load_wetlab_results(path: Path) -> list[WetLabResult]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("records", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("wet-lab JSON must be a list or {'records': [...]}")
    records = [WetLabResult.model_validate(row) for row in rows]
    raw_hash = sha256(path.read_bytes()).hexdigest()
    for record in records:
        record.raw_data_sha256 = raw_hash
    if len({record.record_key for record in records}) != len(records):
        raise ValueError("duplicate_wetlab_record_identity")
    return records
