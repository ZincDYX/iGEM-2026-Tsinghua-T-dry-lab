"""Group real replicate records; time-course variation is not replicate CV."""
from __future__ import annotations
from collections import defaultdict
from statistics import mean, stdev
from .models import WetLabResult

def replicate_variation(records: list[WetLabResult]) -> dict[tuple[str, str], float | None]:
    grouped: dict[tuple[str, str], list[WetLabResult]] = defaultdict(list)
    for record in records:
        grouped[(record.construct_id, record.condition_id)].append(record)
    result: dict[tuple[str, str], float | None] = {}
    for key, group in grouped.items():
        ids = {record.replicate_id for record in group}
        if len(ids) < 2:
            result[key] = None
            continue
        finals = [values[-1] for record in group for values in record.metabolites.values() if values]
        avg = mean(finals) if finals else 0
        result[key] = stdev(finals) / abs(avg) if len(finals) >= 2 and avg else None
    return result
