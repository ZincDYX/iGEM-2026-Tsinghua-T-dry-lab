from __future__ import annotations

import numpy as np
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from scipy.optimize import least_squares


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


def fit_scale_parameter(predicted: list[float], observed: list[float], *, parameter_name: str = "effective_scale", bounds: tuple[float, float] = (0.0, 10.0), bootstrap_samples: int = 100, random_seed: int = 42) -> FitResult:
    """Fit exactly one multiplicative apparent parameter; do not overfit sparse data."""
    if len(predicted) != len(observed) or len(predicted) < 2:
        raise ValueError("at least two paired predicted and observed values are required")
    x, y = np.asarray(predicted, dtype=float), np.asarray(observed, dtype=float)
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)): raise ValueError("fit values must be finite")
    solve = lambda a, b: least_squares(lambda value: value[0] * a - b, x0=[1.0], bounds=([bounds[0]], [bounds[1]])).x[0]
    best = float(solve(x, y)); residuals = (best * x - y)
    ci = None
    if bootstrap_samples > 1:
        rng = np.random.default_rng(random_seed)
        samples = []
        for _ in range(bootstrap_samples):
            indices = rng.integers(0, len(x), len(x))
            samples.append(solve(x[indices], y[indices]))
        ci = (float(np.quantile(samples, .025)), float(np.quantile(samples, .975)))
    warning = "few_timepoints_or_conditions" if len(x) < 4 else None
    return FitResult(parameter_name=parameter_name, best_fit=best, confidence_interval=ci, rmse=float(np.sqrt(np.mean(residuals ** 2))), residuals=residuals.tolist(), identifiability_warning=warning)


def fit_mechanistic_parameter(*, parameter_name: str, initial_value: float, bounds: tuple[float, float], observed: list[float], predictor,
                              bootstrap_samples: int = 0, replicate_blocks: list[list[int]] | None = None) -> FitResult:
    """Fit one parameter; check numerical sensitivity, not merely zero residual.

    The objective is unweighted squared error, not a likelihood with an invented
    noise variance. A profile is diagnostic only. Confidence intervals require
    declared whole biological-replicate blocks; times are never IID units.
    """
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
    def solve(indices):
        # Unit-interval parameter scaling is numerical, not a biological prior.
        return least_squares(lambda coordinate: predict(bounds[0] + width*coordinate[0])[indices] - y[indices],
                             x0=[(initial_value-bounds[0])/width],bounds=([0.], [1.]),
                             xtol=1e-10,ftol=1e-10,gtol=1e-10)
    solved = solve(np.arange(len(y)))
    coordinate = float(solved.x[0])
    best = bounds[0] + width*coordinate
    prediction = predict(best)
    residuals = prediction - y
    profile_values = np.unique(np.r_[np.linspace(bounds[0],bounds[1],9),best])
    profile_predictions = np.asarray([predict(value) for value in profile_values])
    profile_objective = np.sum((profile_predictions-y)**2,axis=1)
    numerical_floor = 64*np.finfo(float).eps*max(float(np.max(np.abs(profile_predictions))),float(np.max(np.abs(y))),np.finfo(float).tiny)
    profile_span = float(np.max(np.ptp(profile_predictions,axis=0)))
    objective_span = float(np.ptp(profile_objective))
    objective_floor = 64*np.finfo(float).eps*max(float(np.max(profile_objective)),np.finfo(float).tiny)
    step = np.cbrt(np.finfo(float).eps)
    left,right = max(0.,coordinate-step),min(1.,coordinate+step)
    jacobian = (predict(bounds[0]+width*right)-predict(bounds[0]+width*left))/(right-left)
    sensitivity = float(np.linalg.norm(jacobian))
    status,warning = "estimated",None
    if not solved.success:
        status,warning = "solver_failed","optimizer_did_not_converge"
    elif profile_span <= numerical_floor or objective_span <= objective_floor or sensitivity <= numerical_floor*np.sqrt(len(y)):
        status,warning = "unidentifiable","flat_or_zero_local_parameter_sensitivity"
    elif solved.active_mask[0] != 0 or coordinate <= step or coordinate >= 1-step:
        status,warning = "boundary_limited","optimum_at_declared_parameter_bound"
    diagnostics = {"optimizer_success":bool(solved.success),"optimizer_status":int(solved.status),
                   "optimizer_message":str(solved.message),"nfev":int(solved.nfev),"optimality":float(solved.optimality),
                   "diagnostic_optimizer_value":best,"bound_hit":bool(solved.active_mask[0] or coordinate<=step or coordinate>=1-step),
                   "scaled_parameter_jacobian_norm":sensitivity,"profile_prediction_span":profile_span,
                   "profile_objective_span":objective_span,
                   "profile_parameter_values":profile_values.tolist(),"profile_squared_error":profile_objective.tolist(),
                   "objective":"unweighted_squared_error_no_variance_assumed",
                   "identifiability_scope":"numerical_local_sensitivity_and_coarse_profile_not_practical_identifiability_proof"}
    if status == "unidentifiable":
        diagnostics["required_information"] = ["confirmed_active_substrate_and_reaction_under_measured_condition",
            "parameter_sensitive_substrate_or_product_time_series", "independent_biological_replicates_or_distinct_experimental_excitation"]
    ci = None
    if bootstrap_samples > 1 and status == "estimated":
        if replicate_blocks is None or len(replicate_blocks)<2:
            warning="replicate_block_bootstrap_requires_declared_biological_replicates"
        else:
            flat=[index for block in replicate_blocks for index in block]
            if any(not block for block in replicate_blocks) or sorted(flat)!=list(range(len(y))):
                raise ValueError("replicate_blocks_must_partition_actual_observations")
            rng=np.random.default_rng(42)
            samples=[]
            for _ in range(bootstrap_samples):
                indices=np.concatenate([replicate_blocks[i] for i in rng.integers(0,len(replicate_blocks),len(replicate_blocks))])
                sample=solve(indices)
                if (not sample.success or sample.active_mask[0] or not step<float(sample.x[0])<1-step or
                        np.linalg.norm(sample.jac)<=numerical_floor*np.sqrt(len(indices))):
                    warning="replicate_block_bootstrap_contains_failed_boundary_or_flat_fits"
                    break
                samples.append(bounds[0]+width*float(sample.x[0]))
            if len(samples)==bootstrap_samples:
                ci=(float(np.quantile(samples,.025)),float(np.quantile(samples,.975)))
    return FitResult(parameter_name=parameter_name,best_fit=best if status=="estimated" else None,status=status,
                     confidence_interval=ci,rmse=float(np.sqrt(np.mean(residuals**2))),residuals=residuals.tolist(),
                     identifiability_warning=warning,diagnostics=diagnostics)
