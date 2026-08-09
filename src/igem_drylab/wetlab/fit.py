from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import least_squares


class FitResult(BaseModel):
    parameter_name: str
    best_fit: float
    confidence_interval: tuple[float, float] | None = None
    rmse: float = Field(ge=0)
    residuals: list[float]
    identifiability_warning: str | None = None


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


def fit_mechanistic_parameter(*, parameter_name: str, initial_value: float, bounds: tuple[float, float], observed: list[float], predictor, bootstrap_samples: int = 100) -> FitResult:
    """Fit one declared parameter through a caller-supplied production simulator."""
    if len(observed) < 4:
        raise ValueError("identifiability_warning:fewer_than_four_timepoints")
    if not bounds[0] <= initial_value <= bounds[1] or bounds[0] >= bounds[1]:
        raise ValueError("invalid fit bounds or initial value")
    y = np.asarray(observed, dtype=float)
    def solve(indices: np.ndarray) -> float:
        return float(least_squares(lambda value: predictor(float(value[0]))[indices] - y[indices], x0=[initial_value], bounds=([bounds[0]], [bounds[1]])).x[0])
    indices = np.arange(len(y)); best = solve(indices); residuals = predictor(best) - y
    ci = None
    if bootstrap_samples > 1:
        rng = np.random.default_rng(42); samples = [solve(rng.integers(0, len(y), len(y))) for _ in range(bootstrap_samples)]
        ci = (float(np.quantile(samples, .025)), float(np.quantile(samples, .975)))
    return FitResult(parameter_name=parameter_name, best_fit=best, confidence_interval=ci, rmse=float(np.sqrt(np.mean(residuals ** 2))), residuals=residuals.tolist())
