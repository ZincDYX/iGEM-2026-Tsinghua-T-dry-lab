"""One explicit residual-significance contract for M5 diagnoses."""
from __future__ import annotations

from pydantic import BaseModel


class ResidualSignificance(BaseModel):
    significant: bool | None
    threshold: float | None = None
    uncertainty_term: float | None = None
    reason: str


def interpret_measurement_uncertainty(value: float | None, uncertainty_type: str | None) -> tuple[float | None, str]:
    """Return an additive uncertainty allowance or an explicit non-interpretation reason.

    SD is retained as the reported one-standard-deviation allowance.  SEM is
    converted to an approximate 95% normal interval (1.96 × SEM).  A scalar CI
    is usable only when the measurement contract states it is a half-width;
    the current WetLabResult contract does not state that, so scalar CI values
    are deliberately not interpreted.
    """
    if value is None:
        return None, "uncertainty_missing"
    if uncertainty_type == "sd":
        return value, "reported_sd"
    if uncertainty_type == "sem":
        return 1.96 * value, "normal_95_from_sem"
    if uncertainty_type == "ci":
        return None, "uncertainty_not_interpretable_scalar_ci"
    return None, "uncertainty_not_interpretable"


def evaluate_residual_significance(
    evidence: dict[str, dict[str, object]],
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
    tolerance_configured: bool,
    require_interpretable_uncertainty: bool,
) -> ResidualSignificance:
    """Evaluate all residuals exactly once without inventing a tolerance."""
    thresholds: list[float] = []
    residuals: list[float] = []
    uncertainty_terms: list[float] = []
    reasons: list[str] = []
    for item in evidence.values():
        residual = item.get("residual_final")
        if residual is None:
            continue
        uncertainty, reason = interpret_measurement_uncertainty(
            item.get("measurement_uncertainty") if isinstance(item.get("measurement_uncertainty"), (int, float)) else None,
            item.get("measurement_uncertainty_type") if isinstance(item.get("measurement_uncertainty_type"), str) else None,
        )
        if require_interpretable_uncertainty and not tolerance_configured and uncertainty is None:
            reasons.append(reason)
            continue
        observed = float(item.get("observed_final") or 0.0)
        predicted = float(item.get("predicted_final") or 0.0)
        allowance = absolute_tolerance + relative_tolerance * max(abs(observed), abs(predicted), 1e-12)
        if uncertainty is not None:
            allowance += uncertainty
            uncertainty_terms.append(uncertainty)
        thresholds.append(allowance)
        residuals.append(abs(float(residual)))
    if not residuals:
        return ResidualSignificance(significant=None, reason=reasons[0] if reasons else "no_quantified_residual")
    return ResidualSignificance(
        significant=any(residual > threshold for residual, threshold in zip(residuals, thresholds, strict=True)),
        threshold=max(thresholds),
        uncertainty_term=max(uncertainty_terms) if uncertainty_terms else 0.0,
        reason="residual_exceeds_combined_tolerance" if any(residual > threshold for residual, threshold in zip(residuals, thresholds, strict=True)) else "residual_within_combined_tolerance",
    )
