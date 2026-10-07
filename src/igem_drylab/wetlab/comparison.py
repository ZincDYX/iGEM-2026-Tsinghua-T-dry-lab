"""Trajectory-aware M4-to-wet-lab comparison with explicit censoring and units."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from .fit import FitResult, fit_scale_parameter
from .models import WetLabResult
from .canonical import canonicalize_metabolite
from igem_drylab.prediction import observe_prediction


class M5ComparisonSeries(BaseModel):
    """Persist the values already aligned by the existing comparison, not a replay."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["m5-comparison-series-v1"] = "m5-comparison-series-v1"
    experiment_id: str
    construct_id: str
    condition_id: str
    replicate_id: str
    raw_data_sha256: str | None
    compartment: str | None
    concentration_basis: str | None
    time_unit: Literal["h"] = "h"
    concentration_unit: Literal["uM"] = "uM"
    source_time_unit: str
    source_concentration_unit: str
    comparison_adapter: Literal["prediction_contract", "legacy_trajectory"]
    time: list[float]
    observed: list[float]
    predicted: list[float]
    residual_observed_minus_predicted: list[float | None]
    censor_mask: list[str]
    lod: float | None
    loq: float | None
    observation_kind: str
    uncertainty: list[float] | None
    uncertainty_type: str | None
    parameter_approval: Literal["not_granted_by_display"] = "not_granted_by_display"


class MetaboliteComparison(BaseModel):
    metabolite_id: str
    residual_final: float | None = None
    observed_final: float | None = None
    predicted_final: float | None = None
    trend_agreement: bool | None = None
    aligned_timepoints: int = 0
    quantified_indices: list[int] = Field(default_factory=list)
    final_quantified_index: int | None = None
    final_quantified_time_h: float | None = None
    residual_unit: str = "uM"
    censor_mask: list[str] = Field(default_factory=list)
    comparison_status: str
    fit: FitResult | None = None
    display_series: M5ComparisonSeries | None = None


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
    contract = data.get("prediction_contract")
    trajectory_unit = contract.get("concentration_unit") if contract else data.get("concentration_unit")
    if trajectory_unit != "uM":
        raise ValueError(f"unsupported_trajectory_concentration_unit:{trajectory_unit}")
    if result.metabolite_concentration_unit is None:
        raise ValueError("missing_wetlab_concentration_unit")
    if contract:
        time, predicted_series = observe_prediction(contract, result)
    else:
        if result.measurement_compartment not in {None, "intracellular"}:
            raise ValueError("legacy_prediction_has_no_requested_compartment_adapter")
        if "time" not in data or not all(f"x{name}" in data for name in result.metabolites if name in {"13", "15"}):
            raise ValueError("missing_trajectory_model_adapter")
        time = np.asarray(data["time"], dtype=float)
        predicted_series = {name: np.asarray(data[f"x{name}"], dtype=float) for name in ("13", "15") if f"x{name}" in data}
    observed_time = np.asarray(result.time_hours(), dtype=float)
    comparisons: dict[str, MetaboliteComparison] = {}
    for metabolite in ("13", "15"):
        raw_observed = result.metabolites.get(metabolite)
        if raw_observed is None:
            continue
        try:
            canonical = canonicalize_metabolite(result, metabolite)
            observed, lod, loq = canonical.concentration_uM, canonical.lod_uM, canonical.loq_uM
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
        if metabolite not in predicted_series:
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, comparison_status="model_does_not_predict_observable")
            continue
        predicted_all = np.interp(observed_time, time, predicted_series[metabolite])
        mask = canonical.censor_mask
        display_series = M5ComparisonSeries(
            experiment_id=result.experiment_id,construct_id=result.construct_id,
            condition_id=result.condition_id,replicate_id=result.replicate_id,
            raw_data_sha256=result.raw_data_sha256,compartment=result.measurement_compartment,
            concentration_basis=result.concentration_basis,source_time_unit=result.metabolite_time_unit,
            source_concentration_unit=result.metabolite_concentration_unit,
            comparison_adapter="prediction_contract" if contract else "legacy_trajectory",
            time=observed_time.tolist(),observed=list(observed),predicted=predicted_all.tolist(),
            residual_observed_minus_predicted=[float(observed[i]-predicted_all[i]) if mask[i]=="quantified" else None for i in range(len(observed))],
            censor_mask=mask,lod=lod,loq=loq,observation_kind=result.observation_kind,
            uncertainty=canonical.uncertainty_uM,uncertainty_type=canonical.uncertainty_type,
        )
        selected = [index for index, flag in enumerate(mask) if flag == "quantified"]
        if not selected:
            comparisons[metabolite] = MetaboliteComparison(metabolite_id=metabolite, censor_mask=mask, comparison_status="all_observations_censored", display_series=display_series)
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
            quantified_indices=selected,
            final_quantified_index=final_index,
            final_quantified_time_h=float(observed_time[final_index]),
            censor_mask=mask,
            comparison_status="trajectory_aligned" if len(selected) >= 2 else "endpoint_only",
            fit=fit,
            display_series=display_series,
        )
    return comparisons
