"""Trajectory-aware M4-to-wet-lab comparison with explicit censoring and units."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from igem_drylab.parameters.dimensions import normalize_concentration
from .fit import FitResult, fit_scale_parameter
from .models import WetLabResult


class MetaboliteComparison(BaseModel):
    metabolite_id: str
    residual_final: float | None = None
    observed_final: float | None = None
    predicted_final: float | None = None
    trend_agreement: bool | None = None
    aligned_timepoints: int = 0
    censor_mask: list[str] = Field(default_factory=list)
    comparison_status: str
    fit: FitResult | None = None


def _censor_mask(values: list[float], lod: float | None, loq: float | None) -> list[str]:
    return [
        "below_lod" if lod is not None and value < lod
        else "below_loq" if loq is not None and value < loq
        else "quantified"
        for value in values
    ]


def compare_prediction(trajectory_path: Path, result: WetLabResult) -> dict[str, MetaboliteComparison]:
    """Compare only quantified observations, never treating LOD/LOQ values as exact.

    Both trajectory and wet-lab values are required to declare a concentration
    unit.  Production trajectories use uM; unsupported values fail fast.
    """
    data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    trajectory_unit = data.get("concentration_unit")
    if trajectory_unit != "uM":
        raise ValueError(f"unsupported_trajectory_concentration_unit:{trajectory_unit}")
    if result.metabolite_concentration_unit is None:
        raise ValueError("missing_wetlab_concentration_unit")
    time = np.asarray(data["time"], dtype=float)
    observed_time = np.asarray(result.time_hours(), dtype=float)
    comparisons: dict[str, MetaboliteComparison] = {}
    for metabolite in ("13", "15"):
        raw_observed = result.metabolites.get(metabolite)
        if raw_observed is None:
            continue
        try:
            observed = [normalize_concentration(value, result.metabolite_concentration_unit) for value in raw_observed]
            lod = normalize_concentration(result.metabolite_lod[metabolite], result.metabolite_concentration_unit) if metabolite in result.metabolite_lod else None
            loq = normalize_concentration(result.metabolite_loq[metabolite], result.metabolite_concentration_unit) if metabolite in result.metabolite_loq else None
        except ValueError as error:
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, comparison_status=str(error))
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
        predicted_all = np.interp(observed_time, time, np.asarray(data[f"x{metabolite}"], dtype=float))
        mask = _censor_mask(observed, lod, loq)
        selected = [index for index, flag in enumerate(mask) if flag == "quantified"]
        if not selected:
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, censor_mask=mask, comparison_status="all_observations_censored")
            continue
        predicted = predicted_all[selected]
        measured = np.asarray([observed[index] for index in selected], dtype=float)
        trend = bool((measured[-1] - measured[0]) * (predicted[-1] - predicted[0]) >= 0) if len(selected) >= 2 else None
        # A time series is not an IID bootstrap sample.  This descriptive fit
        # intentionally carries no confidence interval.
        fit = fit_scale_parameter(predicted.tolist(), measured.tolist(), bootstrap_samples=0) if len(selected) >= 2 and np.any(predicted > 0) else None
        final_index = selected[-1]
        comparisons[metabolite] = MetaboliteComparison(
            metabolite_id=metabolite,
            residual_final=float(observed[final_index] - predicted_all[final_index]),
            observed_final=float(observed[final_index]),
            predicted_final=float(predicted_all[final_index]),
            trend_agreement=trend,
            aligned_timepoints=len(selected),
            censor_mask=mask,
            comparison_status="trajectory_aligned" if len(selected) >= 2 else "endpoint_only",
            fit=fit,
        )
    return comparisons
