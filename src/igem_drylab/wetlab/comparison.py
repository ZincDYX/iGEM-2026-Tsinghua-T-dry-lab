"""Deterministic M4-to-wet-lab comparison; no implicit biological mapping."""

from __future__ import annotations

import numpy as np

from .fit import FitResult, fit_scale_parameter
from .models import WetLabResult


def compare_prediction(predicted_15: float, result: WetLabResult) -> tuple[float | None, bool | None, float | None, FitResult | None]:
    observed = result.metabolites.get("15", [])
    if not observed:
        return None, None, None, None
    residual = float(observed[-1] - predicted_15)
    trend = None
    if len(observed) >= 2:
        trend = bool((observed[-1] - observed[0]) * predicted_15 >= 0)
    variation = _coefficient_variation(observed)
    fit = fit_scale_parameter([predicted_15] * len(observed), observed, bootstrap_samples=20) if len(observed) >= 2 and predicted_15 > 0 else None
    return residual, trend, variation, fit


def _coefficient_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = float(np.mean(values))
    return None if mean == 0 else float(np.std(values, ddof=1) / abs(mean))
