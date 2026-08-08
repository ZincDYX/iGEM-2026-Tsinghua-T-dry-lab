"""Trajectory-aware M4-to-wet-lab comparison."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .fit import FitResult, fit_scale_parameter
from .models import WetLabResult

def compare_prediction(trajectory_path: Path, result: WetLabResult) -> tuple[float | None, bool | None, float | None, FitResult | None, str]:
    data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    observed = result.metabolites.get("15", [])
    if not observed or not result.metabolite_time: return None, None, None, None, "no_observed_15"
    predicted = np.interp(np.asarray(result.metabolite_time, dtype=float), np.asarray(data["time"], dtype=float), np.asarray(data["x15"], dtype=float))
    residual = float(observed[-1] - predicted[-1])
    trend = bool((observed[-1] - observed[0]) * (predicted[-1] - predicted[0]) >= 0) if len(observed) >= 2 else None
    if len(observed) < 2: return residual, trend, None, None, "endpoint_only"
    fit = fit_scale_parameter(predicted.tolist(), observed, bootstrap_samples=20)
    return residual, trend, None, fit, "trajectory_aligned"
