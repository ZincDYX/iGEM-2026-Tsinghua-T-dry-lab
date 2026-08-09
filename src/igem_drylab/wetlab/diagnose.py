from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DiscrepancyDiagnosis(BaseModel):
    category: Literal["DATA_QUALITY_ERROR", "IMPLEMENTATION_ERROR", "NO_SIGNIFICANT_DISCREPANCY", "PARAMETER_MISMATCH", "MODEL_MISMATCH", "INSUFFICIENT_INFORMATION"]
    evidence: list[str]


def diagnose_discrepancy(*, qc_passed: bool, replicate_variation: float | None, abundance_ratio: float | None, trend_agreement: bool | None, systematic_directional_error: bool | None, significant_residual: bool | None = None) -> DiscrepancyDiagnosis:
    """Deterministic diagnostic precedence; no LLM classification is involved."""
    if not qc_passed or (replicate_variation is not None and replicate_variation > 0.5): return DiscrepancyDiagnosis(category="DATA_QUALITY_ERROR", evidence=["QC failure or high replicate variation"])
    # Abundance-based implementation diagnosis is intentionally disabled until
    # abundance measurements have a reviewed expected-value contract.
    if systematic_directional_error: return DiscrepancyDiagnosis(category="MODEL_MISMATCH", evidence=["multiple conditions have systematic directional error"])
    if significant_residual is None: return DiscrepancyDiagnosis(category="INSUFFICIENT_INFORMATION", evidence=["missing_discrepancy_threshold"])
    if significant_residual is False: return DiscrepancyDiagnosis(category="NO_SIGNIFICANT_DISCREPANCY", evidence=["residual is within uncertainty and tolerance"])
    if trend_agreement is True: return DiscrepancyDiagnosis(category="PARAMETER_MISMATCH", evidence=["trend agrees but amplitude differs"])
    return DiscrepancyDiagnosis(category="INSUFFICIENT_INFORMATION", evidence=["no discriminating deterministic evidence"])
