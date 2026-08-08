"""Single source of truth for machine-readable M3/M4 parameter requirements."""

from __future__ import annotations

from pydantic import BaseModel


class ParameterRequirement(BaseModel):
    name: str
    parameter_type: str
    optional: bool = False


def m3_requirements() -> list[ParameterRequirement]:
    species = ("pt", "oc", "dmt", "x9", "x10", "x11", "x13", "x15")
    return [ParameterRequirement(name="phi", parameter_type="phi")] + [ParameterRequirement(name=f"{item}_total", parameter_type="abundance") for item in species] + [ParameterRequirement(name=f"partition_{item}", parameter_type="kp") for item in species]


def m4_requirements() -> list[ParameterRequirement]:
    return [ParameterRequirement(name=name, parameter_type=kind) for name, kind in [
        ("phi", "phi"), ("pt_total", "abundance"), ("oc_total", "abundance"), ("dmt_total", "abundance"),
        ("kcat_pt", "kcat"), ("km_pt", "km"), ("kcat_oc", "kcat"), ("km_oc", "km"), ("kcat_dmt_9", "kcat"), ("km_dmt_9", "km"), ("kcat_dmt_11", "kcat"), ("km_dmt_11", "km"),
        *[(f"partition_{item}", "kp") for item in ("pt", "oc", "dmt", "x9", "x10", "x11", "x13", "x15")],
        *[(f"activity_{phase}_{enzyme}", "activity_ratio") for phase in ("dense", "dilute") for enzyme in ("pt", "oc", "dmt")],
    ]]
