from __future__ import annotations

from statistics import median

from pydantic import BaseModel, Field

from .models import WetLabResult


class QcReport(BaseModel):
    experiment_id: str
    replicate_id: str
    passed: bool
    flags: list[str] = Field(default_factory=list)
    outlier_flags: dict[str, bool] = Field(default_factory=dict)
    censor_masks: dict[str, list[str]] = Field(default_factory=dict)


def quality_control(records: list[WetLabResult]) -> list[QcReport]:
    """Flag invalid/missing measurements without deleting any observation."""
    reports: list[QcReport] = []
    for record in records:
        flags: list[str] = []
        if not record.control_available: flags.append("control_unavailable")
        if record.biological_replicate_count < 2: flags.append("fewer_than_two_biological_replicates")
        if not record.metabolite_time: flags.append("metabolite_time_missing")
        masks: dict[str, list[str]] = {}
        for species, values in record.metabolites.items():
            if len(values) != len(record.metabolite_time): flags.append(f"time_length_mismatch:{species}")
            if any(value < 0 for value in values): flags.append(f"negative_metabolite:{species}")
            lod = record.metabolite_lod.get(species); loq = record.metabolite_loq.get(species)
            masks[species] = [
                "below_lod" if lod is not None and value < lod
                else "below_loq" if loq is not None and value < loq
                else "quantified"
                for value in values
            ]
        if any(value < 0 for value in record.protein_abundance.values()): flags.append("negative_protein_abundance")
        reports.append(QcReport(experiment_id=record.experiment_id, replicate_id=record.replicate_id, passed=not any(flag.startswith(("negative", "metabolite_time", "time_length")) for flag in flags), flags=flags, censor_masks=masks))
    _flag_replicate_outliers(records, reports)
    return reports


def _flag_replicate_outliers(records: list[WetLabResult], reports: list[QcReport]) -> None:
    grouped: dict[tuple[str, str, str, float], list[tuple[int, float]]] = {}
    for index, record in enumerate(records):
        for species, values in record.metabolites.items():
            times = record.time_hours()
            if values and len(values) == len(times):
                key = (record.construct_id, record.condition_id, species, times[-1])
                grouped.setdefault(key, []).append((index, values[-1]))
    for values in grouped.values():
        if len(values) < 3: continue
        centre = median(value for _, value in values); deviations = [abs(value - centre) for _, value in values]; mad = median(deviations)
        if mad == 0: continue
        for index, value in values:
            if abs(value - centre) / mad > 3.5:
                reports[index].outlier_flags["final_metabolite"] = True
                reports[index].flags.append("outlier_flagged_not_removed")
