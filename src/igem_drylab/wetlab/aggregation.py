"""Group real replicate records; time-course variation is not replicate CV."""
from __future__ import annotations
from collections import defaultdict
from statistics import mean, stdev
from .models import WetLabResult

def replicate_variation(records: list[WetLabResult]) -> dict[tuple[str, str, str], float | None]:
    """Final-time CV separated by construct, condition, and metabolite."""
    grouped: dict[tuple[str, str, str], list[tuple[str, float]]] = defaultdict(list)
    for record in records:
        for metabolite, values in record.metabolites.items():
            if values:
                grouped[(record.construct_id, record.condition_id, metabolite)].append((record.replicate_id, values[-1]))
    result: dict[tuple[str, str, str], float | None] = {}
    for key, group in grouped.items():
        ids = {replicate for replicate, _ in group}
        if len(ids) < 2:
            result[key] = None
            continue
        finals = [value for _, value in group]
        avg = mean(finals) if finals else 0
        result[key] = stdev(finals) / abs(avg) if len(finals) >= 2 and avg else None
    return result
