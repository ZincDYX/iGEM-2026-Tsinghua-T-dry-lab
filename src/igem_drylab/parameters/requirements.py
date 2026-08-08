"""Single source of truth for the M3/M4 parameter contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Dimension = Literal["dimensionless", "concentration", "rate"]


class ParameterRequirement(BaseModel):
    name: str
    parameter_type: str
    dimension: Dimension
    canonical_unit: str = "1"
    enzyme_id: str | None = None
    substrate_id: str | None = None
    product_id: str | None = None
    optional: bool = False


def _requirement(name: str, parameter_type: str, **identity: str | None) -> ParameterRequirement:
    if parameter_type in {"phi", "kp", "activity_ratio", "hill_coefficient"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", **identity)
    if parameter_type in {"km", "kd", "abundance"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="concentration", canonical_unit="uM", **identity)
    if parameter_type in {"kcat", "degradation_rate", "export_rate"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="rate", canonical_unit="1/s", **identity)
    return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", **identity)


def m3_requirements() -> list[ParameterRequirement]:
    """M3 only uses enzyme abundance/Kp, not fixed metabolite state totals."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"{enzyme}_total", "abundance", enzyme_id=enzyme.upper()) for enzyme in ("pt", "oc", "dmt")],
        *[_requirement(f"partition_{species}", "kp") for species in ("pt", "oc", "dmt")],
    ]


def m4_requirements() -> list[ParameterRequirement]:
    return [
        *m3_requirements(),
        _requirement("kcat_pt", "kcat", enzyme_id="PT", substrate_id="9", product_id="10"),
        _requirement("km_pt", "km", enzyme_id="PT", substrate_id="9"),
        _requirement("kcat_oc", "kcat", enzyme_id="OC", substrate_id="10", product_id="11"),
        _requirement("km_oc", "km", enzyme_id="OC", substrate_id="10"),
        _requirement("kcat_dmt_9", "kcat", enzyme_id="DMT", substrate_id="9", product_id="13"),
        _requirement("km_dmt_9", "km", enzyme_id="DMT", substrate_id="9"),
        _requirement("kcat_dmt_11", "kcat", enzyme_id="DMT", substrate_id="11", product_id="15"),
        _requirement("km_dmt_11", "km", enzyme_id="DMT", substrate_id="11"),
        *[_requirement(f"partition_x{species}", "kp") for species in ("9", "10", "11", "13", "15")],
        *[_requirement(f"activity_{phase}_{enzyme}", "activity_ratio", enzyme_id=enzyme.upper()) for phase in ("dense", "dilute") for enzyme in ("pt", "oc", "dmt")],
    ]
