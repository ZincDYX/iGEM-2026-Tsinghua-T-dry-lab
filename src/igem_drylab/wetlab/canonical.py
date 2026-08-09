"""Single canonical preparation path for real wet-lab metabolite series."""
from __future__ import annotations

from pydantic import BaseModel, Field

from igem_drylab.parameters.dimensions import normalize_concentration
from .models import WetLabResult


class CanonicalMetaboliteSeries(BaseModel):
    metabolite_id: str
    time_h: list[float]
    concentration_uM: list[float]
    uncertainty_uM: list[float] | None = None
    uncertainty_type: str | None = None
    lod_uM: float | None = None
    loq_uM: float | None = None
    censor_mask: list[str] = Field(default_factory=list)


def canonicalize_metabolite(result: WetLabResult, metabolite_id: str) -> CanonicalMetaboliteSeries:
    """Convert one validated raw series without mutating the source record."""
    values = result.metabolites.get(metabolite_id)
    if values is None:
        raise ValueError(f"missing_metabolite:{metabolite_id}")
    if result.metabolite_concentration_unit is None:
        raise ValueError("missing_wetlab_concentration_unit")
    concentrations = [normalize_concentration(value, result.metabolite_concentration_unit) for value in values]
    uncertainty = result.metabolite_uncertainty.get(metabolite_id)
    uncertainty_uM = [normalize_concentration(value, result.metabolite_concentration_unit) for value in uncertainty] if uncertainty is not None else None
    lod = normalize_concentration(result.metabolite_lod[metabolite_id], result.metabolite_concentration_unit) if metabolite_id in result.metabolite_lod else None
    loq = normalize_concentration(result.metabolite_loq[metabolite_id], result.metabolite_concentration_unit) if metabolite_id in result.metabolite_loq else None
    mask = ["below_lod" if lod is not None and value < lod else "below_loq" if loq is not None and value < loq else "quantified" for value in concentrations]
    return CanonicalMetaboliteSeries(metabolite_id=metabolite_id, time_h=result.time_hours(), concentration_uM=concentrations, uncertainty_uM=uncertainty_uM, uncertainty_type=result.metabolite_uncertainty_type, lod_uM=lod, loq_uM=loq, censor_mask=mask)
