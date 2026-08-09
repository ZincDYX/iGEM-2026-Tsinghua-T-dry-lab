"""Group real replicate records; time-course variation is not replicate CV."""
from __future__ import annotations
from collections import defaultdict
from statistics import mean, stdev
from .canonical import canonicalize_metabolite
from .models import WetLabResult

def replicate_variation(records: list[WetLabResult]) -> dict[tuple[str, str, str, float], float | None]:
    """CV only for biological replicates sharing construct, condition, metabolite, and final time."""
    grouped: dict[tuple[str, str, str, float], list[tuple[str, float]]] = defaultdict(list)
    observed_keys: set[tuple[str, str, str, float]] = set()
    for record in records:
        for metabolite in record.metabolites:
            series = canonicalize_metabolite(record, metabolite)
            for time_h, value, censor in zip(series.time_h, series.concentration_uM, series.censor_mask, strict=True):
                observed_keys.add((record.construct_id, record.condition_id, metabolite, time_h))
                if censor == "quantified":
                    grouped[(record.construct_id, record.condition_id, metabolite, time_h)].append((record.replicate_id, value))
    result: dict[tuple[str, str, str, float], float | None] = {}
    for key in observed_keys:
        values = grouped[key]
        ids = {replicate for replicate, _ in values}
        if len(ids) < 2:
            result[key] = None
            continue
        quantified = [value for _, value in values]
        avg = mean(quantified) if quantified else 0
        result[key] = stdev(quantified) / abs(avg) if len(quantified) >= 2 and avg else None
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
