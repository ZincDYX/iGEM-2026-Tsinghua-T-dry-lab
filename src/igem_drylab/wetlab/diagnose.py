from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DiscrepancyDiagnosis(BaseModel):
    category: Literal["DATA_QUALITY_ERROR", "IMPLEMENTATION_ERROR", "PARAMETER_MISMATCH", "MODEL_MISMATCH", "INSUFFICIENT_INFORMATION"]
    evidence: list[str]


def diagnose_discrepancy(*, qc_passed: bool, replicate_variation: float | None, abundance_ratio: float | None, trend_agreement: bool | None, systematic_directional_error: bool | None) -> DiscrepancyDiagnosis:
    """Deterministic diagnostic precedence; no LLM classification is involved."""
    if not qc_passed or (replicate_variation is not None and replicate_variation > 0.5): return DiscrepancyDiagnosis(category="DATA_QUALITY_ERROR", evidence=["QC failure or high replicate variation"])
    if abundance_ratio is not None and abundance_ratio < 0.3: return DiscrepancyDiagnosis(category="IMPLEMENTATION_ERROR", evidence=["measured abundance substantially below expected"])
    if systematic_directional_error: return DiscrepancyDiagnosis(category="MODEL_MISMATCH", evidence=["multiple conditions have systematic directional error"])
    if trend_agreement is True: return DiscrepancyDiagnosis(category="PARAMETER_MISMATCH", evidence=["trend agrees but amplitude differs"])
    return DiscrepancyDiagnosis(category="INSUFFICIENT_INFORMATION", evidence=["no discriminating deterministic evidence"])
