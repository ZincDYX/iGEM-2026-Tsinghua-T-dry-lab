from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class FitResult(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    parameter_name: str
    best_fit: float | None
    status: Literal["estimated", "unidentifiable", "solver_failed", "boundary_limited"] = "estimated"
    confidence_interval: tuple[float, float] | None = None
    rmse: float = Field(ge=0)
    residuals: list[float]
    identifiability_warning: str | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


def _resampling_units(count, replicate_blocks, independent_samples):
    if replicate_blocks is not None:
        flat = [index for block in replicate_blocks for index in block]
        if any(not block for block in replicate_blocks) or sorted(flat) != list(range(count)):
            raise ValueError("replicate_blocks_must_partition_actual_observations")
        return replicate_blocks if len(replicate_blocks) >= 2 else None
    return [[index] for index in range(count)] if independent_samples else None


def fit_scale_parameter(predicted: list[float], observed: list[float], *, parameter_name: str = "effective_scale",
                        bounds: tuple[float, float] = (0.0, 10.0), bootstrap_samples: int = 0, random_seed: int = 42,
                        replicate_blocks: list[list[int]] | None = None, independent_samples: bool = False) -> FitResult:
    """Descriptive bounded linear scale, not a mechanistic parameter estimate.

    No IID time bootstrap. Resampling requires explicitly independent samples
    or whole biological-replicate blocks, never an inferred noise model.
    """
    if len(predicted) != len(observed) or len(predicted) < 2:
        raise ValueError("at least two paired predicted and observed values are required")
    x, y = np.asarray(predicted, dtype=float), np.asarray(observed, dtype=float)
    if not np.all(np.isfinite([*x, *y, *bounds])) or bounds[0] >= bounds[1]:
        raise ValueError("fit values and increasing bounds must be finite")
    magnitude = max(float(np.max(np.abs(x))), float(np.max(np.abs(y))))
    scale = magnitude if magnitude else 1.0
    xs, ys = x / scale, y / scale
    def solve(indices):
        a, b = xs[indices], ys[indices]
        information = float(a @ a)
        return float(np.clip((a @ b) / information, *bounds)) if information else None
    best = solve(np.arange(len(x)))
    status = "unidentifiable" if best is None else "boundary_limited" if best in bounds else "estimated"
    diagnostic_value = best if best is not None else float(np.clip(1.0, *bounds))
    residuals = diagnostic_value * x - y
    warning = {"unidentifiable": "zero_prediction_has_no_scale_information",
               "boundary_limited": "optimum_at_declared_parameter_bound"}.get(status)
    units = _resampling_units(len(x), replicate_blocks, independent_samples)
    ci = None
    if bootstrap_samples > 1 and status == "estimated":
        if units is None:
            warning = "bootstrap_requires_declared_independent_samples_or_biological_replicates"
        else:
            rng = np.random.default_rng(random_seed)
            samples = []
            for _ in range(bootstrap_samples):
                indices = np.concatenate([units[i] for i in rng.integers(0, len(units), len(units))])
                value = solve(indices)
                if value is None or value in bounds:
                    warning = "bootstrap_contains_uninformative_or_boundary_fits"
                    break
                samples.append(value)
            if len(samples) == bootstrap_samples:
                ci = (float(np.quantile(samples, .025)), float(np.quantile(samples, .975)))
    return FitResult(parameter_name=parameter_name, best_fit=best if status == "estimated" else None, status=status,
        confidence_interval=ci, rmse=float(np.linalg.norm(residuals) / np.sqrt(len(y))), residuals=residuals.tolist(),
        identifiability_warning=warning, diagnostics={"fit_kind": "descriptive_multiplicative_scale_not_mechanistic",
        "objective": "unweighted_squared_error_no_variance_assumed", "residual_scale": scale,
        "diagnostic_optimizer_value": diagnostic_value, "squared_error": float(residuals @ residuals),
        "resampling_unit": "biological_replicate_block" if replicate_blocks else "independent_sample" if independent_samples else "none"})


def fit_mechanistic_parameter(*, parameter_name: str, initial_value: float, bounds: tuple[float, float], observed: list[float], predictor,
                              bootstrap_samples: int = 0, replicate_blocks: list[list[int]] | None = None) -> FitResult:
    """One parameter, one common numerical residual scale, unweighted SSE.

    A finite coarse profile supplies restart points, not global uniqueness.
    Confidence intervals require declared whole biological-replicate blocks.
    """
    from scipy.optimize import least_squares
    if len(observed) < 4:
        raise ValueError("identifiability_warning:fewer_than_four_timepoints")
    if not np.all(np.isfinite([*bounds, initial_value, *observed])) or not bounds[0] <= initial_value <= bounds[1] or bounds[0] >= bounds[1]:
        raise ValueError("invalid fit bounds or initial value")
    y = np.asarray(observed, dtype=float)
    def predict(value):
        prediction = np.asarray(predictor(float(value)), dtype=float)
        if prediction.shape != y.shape or not np.all(np.isfinite(prediction)):
            raise ValueError("fit_predictor_requires_finite_aligned_observations")
        return prediction
    width = bounds[1] - bounds[0]
    profile_values = np.unique(np.r_[np.linspace(*bounds, 9), initial_value])
    profile_predictions = np.asarray([predict(value) for value in profile_values])
    magnitude = max(float(np.max(np.abs(profile_predictions))), float(np.max(np.abs(y))))
    scale = magnitude if magnitude else 1.0
    profile_scaled_objective = np.sum(((profile_predictions - y) / scale)**2, axis=1)
    profile_best = float(profile_values[np.argmin(profile_scaled_objective)])
    starts = list(dict.fromkeys([initial_value, profile_best]))
    def solve(indices):
        solutions = [least_squares(lambda coordinate: (predict(bounds[0] + width * coordinate[0])[indices] - y[indices]) / scale,
                                  x0=[(start - bounds[0]) / width], bounds=([0.], [1.]),
                                  xtol=1e-10, ftol=1e-10, gtol=1e-10) for start in starts]
        successful = [item for item in solutions if item.success]
        return min(successful or solutions, key=lambda item: float(item.fun @ item.fun))
    solved = solve(np.arange(len(y)))
    coordinate = float(solved.x[0])
    best = bounds[0] + width * coordinate
    prediction = predict(best)
    residuals = prediction - y
    profile_values = np.r_[profile_values, best]
    profile_predictions = np.vstack([profile_predictions, prediction])
    profile_objective = np.sum((profile_predictions - y)**2, axis=1)
    profile_scaled_objective = np.sum(((profile_predictions - y) / scale)**2, axis=1)
    numerical_floor = 64 * np.finfo(float).eps * scale
    profile_span = float(np.max(np.ptp(profile_predictions, axis=0)))
    objective_span = float(np.ptp(profile_scaled_objective))
    objective_floor = 64 * np.finfo(float).eps * max(float(np.max(profile_scaled_objective)), np.finfo(float).tiny)
    step = np.cbrt(np.finfo(float).eps)
    left, right = max(0., coordinate - step), min(1., coordinate + step)
    jacobian = (predict(bounds[0] + width * right) - predict(bounds[0] + width * left)) / (right - left)
    sensitivity = float(np.linalg.norm(jacobian))
    solution_objective = float(np.sum((residuals / scale)**2))
    inferior = bool(solution_objective > float(np.min(profile_scaled_objective)) + objective_floor)
    status, warning = "estimated", None
    if not solved.success or inferior:
        status, warning = "solver_failed", "solution_inferior_to_evaluated_profile" if inferior else "optimizer_did_not_converge"
    elif profile_span <= numerical_floor or objective_span <= objective_floor or sensitivity <= numerical_floor * np.sqrt(len(y)):
        status, warning = "unidentifiable", "flat_or_zero_local_parameter_sensitivity"
    elif solved.active_mask[0] != 0 or coordinate <= step or coordinate >= 1 - step:
        status, warning = "boundary_limited", "optimum_at_declared_parameter_bound"
    diagnostics = {"optimizer_success": bool(solved.success), "optimizer_status": int(solved.status),
        "optimizer_message": str(solved.message), "nfev": int(solved.nfev), "optimality": float(solved.optimality),
        "diagnostic_optimizer_value": best, "bound_hit": bool(solved.active_mask[0] or coordinate <= step or coordinate >= 1-step),
        "scaled_parameter_jacobian_norm": sensitivity, "profile_prediction_span": profile_span,
        "profile_objective_span": float(np.ptp(profile_objective)),
        "profile_parameter_values": profile_values.tolist(), "profile_squared_error": profile_objective.tolist(),
        "profile_scaled_squared_error": profile_scaled_objective.tolist(), "squared_error": float(residuals @ residuals),
        "residual_scale": scale, "residual_scale_source": "common_max_abs_observation_and_evaluated_profile_predictions",
        "scaled_squared_error": solution_objective, "scaled_residuals": (residuals / scale).tolist(),
        "restart_parameter_values": starts, "solution_inferior_to_profile": inferior,
        "objective": "unweighted_squared_error_no_variance_assumed",
        "identifiability_scope": "numerical_local_sensitivity_and_finite_profile_not_global_uniqueness_or_practical_identifiability_proof"}
    if status == "unidentifiable":
        diagnostics["required_information"] = ["confirmed_active_substrate_and_reaction_under_measured_condition",
            "parameter_sensitive_substrate_or_product_time_series", "independent_biological_replicates_or_distinct_experimental_excitation"]
    units = _resampling_units(len(y), replicate_blocks, False)
    ci = None
    if bootstrap_samples > 1 and status == "estimated":
        if units is None:
            warning = "replicate_block_bootstrap_requires_declared_biological_replicates"
        else:
            rng = np.random.default_rng(42)
            samples = []
            for _ in range(bootstrap_samples):
                indices = np.concatenate([units[i] for i in rng.integers(0, len(units), len(units))])
                sample = solve(indices)
                sample_coordinate = float(sample.x[0])
                sample_floor = 64 * np.finfo(float).eps * max(float(sample.fun @ sample.fun), np.finfo(float).tiny)
                sample_profile = np.sum(((profile_predictions[:, indices] - y[indices]) / scale)**2, axis=1)
                if (not sample.success or sample.active_mask[0] or not step < sample_coordinate < 1-step or
                    np.linalg.norm(sample.jac) <= 64*np.finfo(float).eps*np.sqrt(len(indices)) or
                    float(sample.fun @ sample.fun) > float(np.min(sample_profile)) + sample_floor):
                    warning = "replicate_block_bootstrap_contains_failed_boundary_or_flat_fits"
                    break
                samples.append(bounds[0] + width * sample_coordinate)
            if len(samples) == bootstrap_samples:
                ci = (float(np.quantile(samples, .025)), float(np.quantile(samples, .975)))
    return FitResult(parameter_name=parameter_name, best_fit=best if status == "estimated" else None, status=status,
        confidence_interval=ci, rmse=float(np.linalg.norm(residuals) / np.sqrt(len(y))), residuals=residuals.tolist(),
        identifiability_warning=warning, diagnostics=diagnostics)
