from __future__ import annotations

import json
import math
from hashlib import sha256
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class AssayConditions(BaseModel):
    """Reported experiment facts, never defaults copied from a target project."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    condition_id: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    raw_data_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verified_by: str = Field(min_length=1)
    host: str | None = None
    strain: str | None = None
    temperature_c: float | None = None
    pH: float | None = None
    assay_system: str | None = None
    phase: Literal["dense", "dilute"] | None = None
    enzyme_sequence_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    enzyme_concentration_definition: str | None = None
    cofactor_conditions: str | None = None

    def parameter_conditions(self) -> dict:
        return self.model_dump(exclude_none=True, exclude={"condition_id"})


class MetabolitePartitionMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    dense_concentration_um: float = Field(gt=0)
    dilute_concentration_um: float = Field(gt=0)
    source_reference: str = Field(min_length=1)
    raw_data_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_reference: str = Field(min_length=1)
    recovery_reference: str = Field(min_length=1)
    phase_volume_reference: str = Field(min_length=1)
    assay_condition_id: str | None = None

    @property
    def kp(self) -> float:
        return self.dense_concentration_um / self.dilute_concentration_um


class WetLabResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experiment_id: str
    construct_id: str
    condition_id: str
    replicate_id: str
    assay_conditions: AssayConditions | None = None
    measurement_conditions: dict[str, AssayConditions] = Field(default_factory=dict)
    measurement_condition_ids: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime | None = None
    protein_abundance: dict[str, float] = Field(default_factory=dict)
    imaging: dict[str, float] = Field(default_factory=dict)
    enzyme_activity: dict[str, float] = Field(default_factory=dict)
    partition_measurements: dict[Literal["8", "9", "10", "11", "12", "13", "14", "15"], MetabolitePartitionMeasurement] = Field(default_factory=dict)
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
    assay_mode: Literal["substrate_feeding_functional", "full_pathway_production"] | None = None
    expression_mode: Literal["constitutive", "induced"] | None = None
    input_boundary: dict[str, str | float | None] = Field(default_factory=dict)
    steady_state_confirmation_reference: str | None = None
    measurement_compartment: Literal["intracellular", "extracellular", "total_extract"] | None = None
    concentration_basis: Literal["cell_volume", "medium_volume", "extraction_volume"] | None = None
    extraction_volume_l: float | None = Field(default=None, gt=0)
    raw_data_sha256: str | None = None
    source_replicate_data: list[dict] = Field(default_factory=list)
    notes: str = ""

    def conditions_for(self, source_field: str) -> AssayConditions | None:
        """A measurement override resolves only against verified experiment records."""
        reference = self.measurement_condition_ids.get(source_field)
        if source_field.startswith("partition_measurements."):
            measurement = self.partition_measurements.get(source_field.split(".", 1)[1])
            if measurement and measurement.assay_condition_id:
                if reference and reference != measurement.assay_condition_id:
                    raise ValueError("conflicting_measurement_condition_references")
                reference = measurement.assay_condition_id
        if reference:
            conditions = self.measurement_conditions.get(reference)
            if conditions is None or conditions.condition_id != reference:
                raise ValueError("unverified_measurement_condition_reference:" + reference)
            return conditions
        return self.assay_conditions

    def time_hours(self) -> list[float]:
        divisor = {"h": 1.0, "min": 60.0, "s": 3600.0}[self.metabolite_time_unit]
        return [time / divisor for time in self.metabolite_time]

    @property
    def record_key(self) -> tuple[str, str, str, str]:
        return self.experiment_id, self.construct_id, self.condition_id, self.replicate_id

    @model_validator(mode="after")
    def _validate_series(self) -> "WetLabResult":
        if self.assay_conditions and self.assay_conditions.condition_id != self.condition_id:
            raise ValueError("assay_condition_identity_mismatch")
        if any(key != value.condition_id for key, value in self.measurement_conditions.items()):
            raise ValueError("measurement_condition_identity_mismatch")
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
