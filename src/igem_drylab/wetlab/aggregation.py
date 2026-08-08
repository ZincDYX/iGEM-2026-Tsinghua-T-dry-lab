"""Group real replicate records; time-course variation is not replicate CV."""
from __future__ import annotations
from collections import defaultdict
from statistics import mean, stdev
from .models import WetLabResult

def replicate_variation(records: list[WetLabResult]) -> dict[tuple[str, str, str, float], float | None]:
    """CV only for biological replicates sharing construct, condition, metabolite, and final time."""
    grouped: dict[tuple[str, str, str], list[tuple[str, float, float]]] = defaultdict(list)
    for record in records:
        for metabolite, values in record.metabolites.items():
            times = record.time_hours()
            if values and len(values) == len(times):
                grouped[(record.construct_id, record.condition_id, metabolite)].append((record.replicate_id, times[-1], values[-1]))
    result: dict[tuple[str, str, str, float], float | None] = {}
    for key, group in grouped.items():
        by_time: dict[float, list[tuple[str, float]]] = defaultdict(list)
        for replicate, time_h, value in group:
            by_time[time_h].append((replicate, value))
        for time_h, values in by_time.items():
            ids = {replicate for replicate, _ in values}
            output_key = (*key, time_h)
            if len(ids) < 2:
                result[output_key] = None
                continue
            finals = [value for _, value in values]
            avg = mean(finals) if finals else 0
            result[output_key] = stdev(finals) / abs(avg) if len(finals) >= 2 and avg else None
    return result


def systematic_directional_errors(rows: list[tuple[str, str, str, float | None, bool]]) -> set[tuple[str, str]]:
    """Flag agreement across independent conditions, never merely across replicates."""
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for construct, condition, metabolite, residual, qc_passed in rows:
        if qc_passed and residual is not None:
            grouped[(construct, condition, metabolite)].append(residual)
    condition_residuals = {key: mean(values) for key, values in grouped.items()}
    by_construct_metabolite: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (construct, _condition, metabolite), residual in condition_residuals.items():
        by_construct_metabolite[(construct, metabolite)].append(residual)
    return {key for key, values in by_construct_metabolite.items() if len(values) >= 2 and (all(value > 0 for value in values) or all(value < 0 for value in values))}
