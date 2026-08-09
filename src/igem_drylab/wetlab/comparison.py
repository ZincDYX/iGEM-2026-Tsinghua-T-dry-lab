"""Trajectory-aware, non-extrapolating M4-to-wet-lab comparison."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from pydantic import BaseModel
from .fit import FitResult, fit_scale_parameter
from .models import WetLabResult

class MetaboliteComparison(BaseModel):
    metabolite_id: str
    residual_final: float | None = None
    observed_final: float | None = None
    predicted_final: float | None = None
    trend_agreement: bool | None = None
    aligned_timepoints: int = 0
    comparison_status: str
    fit: FitResult | None = None

def compare_prediction(trajectory_path: Path, result: WetLabResult) -> dict[str, MetaboliteComparison]:
    data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    time = np.asarray(data["time"], dtype=float)
    observed_time = np.asarray(result.time_hours(), dtype=float)
    comparisons: dict[str, MetaboliteComparison] = {}
    for metabolite in ("13", "15"):
        observed = result.metabolites.get(metabolite)
        if observed is None:
            continue
        if observed_time.size != len(observed):
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, comparison_status="invalid_series_length")
            continue
        if observed_time.size == 0:
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, comparison_status="no_observations")
            continue
        if observed_time.min() < time.min() or observed_time.max() > time.max():
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, comparison_status="measurement_outside_simulation_horizon")
            continue
        predicted = np.interp(observed_time, time, np.asarray(data[f"x{metabolite}"], dtype=float))
        trend = bool((observed[-1] - observed[0]) * (predicted[-1] - predicted[0]) >= 0) if len(observed) >= 2 else None
        fit = fit_scale_parameter(predicted.tolist(), observed, bootstrap_samples=20) if len(observed) >= 2 and np.any(predicted > 0) else None
        comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, residual_final=float(observed[-1] - predicted[-1]), observed_final=float(observed[-1]), predicted_final=float(predicted[-1]), trend_agreement=trend, aligned_timepoints=len(observed), comparison_status="trajectory_aligned" if len(observed) >= 2 else "endpoint_only", fit=fit)
    return comparisons
