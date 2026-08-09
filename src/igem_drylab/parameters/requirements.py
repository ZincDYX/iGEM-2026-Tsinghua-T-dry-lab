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
    species_id: str | None = None
    phase: Literal["dense", "dilute"] | None = None
    minimum: float | None = None
    minimum_inclusive: bool = True
    maximum: float | None = None
    blocking: bool = True


def _requirement(name: str, parameter_type: str, **identity: str | None) -> ParameterRequirement:
    if parameter_type in {"phi", "kp", "activity_ratio", "hill_coefficient"}:
        minimum, inclusive = (0.0, True) if parameter_type in {"phi", "activity_ratio"} else (0.0, False)
        maximum = 1.0 if parameter_type == "phi" else None
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", minimum=minimum, minimum_inclusive=inclusive, maximum=maximum, **identity)
    if parameter_type in {"km", "kd", "abundance"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="concentration", canonical_unit="uM", minimum=0.0, minimum_inclusive=parameter_type == "abundance", **identity)
    if parameter_type in {"kcat", "degradation_rate", "export_rate"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="rate", canonical_unit="1/h", minimum=0.0, **identity)
    return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", **identity)


def m3_requirements() -> list[ParameterRequirement]:
    """M3 only uses enzyme abundance/Kp, not fixed metabolite state totals."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"{enzyme}_total", "abundance", enzyme_id=enzyme.upper()) for enzyme in ("pt", "oc", "dmt")],
        *[_requirement(f"partition_{species}", "kp", species_id=species.upper()) for species in ("pt", "oc", "dmt")],
    ]


def m4_requirements(*, include_degradation: bool = False) -> list[ParameterRequirement]:
    requirements = [
        *m3_requirements(),
        _requirement("kcat_pt", "kcat", enzyme_id="PT", substrate_id="9", product_id="10"),
        _requirement("km_pt", "km", enzyme_id="PT", substrate_id="9"),
        _requirement("kcat_oc", "kcat", enzyme_id="OC", substrate_id="10", product_id="11"),
        _requirement("km_oc", "km", enzyme_id="OC", substrate_id="10"),
        _requirement("kcat_dmt_9", "kcat", enzyme_id="DMT", substrate_id="9", product_id="13"),
        _requirement("km_dmt_9", "km", enzyme_id="DMT", substrate_id="9"),
        _requirement("kcat_dmt_11", "kcat", enzyme_id="DMT", substrate_id="11", product_id="15"),
        _requirement("km_dmt_11", "km", enzyme_id="DMT", substrate_id="11"),
        *[_requirement(f"partition_x{species}", "kp", species_id=species) for species in ("9", "10", "11")],
        *[_requirement(f"activity_{phase}_{enzyme}", "activity_ratio", enzyme_id=enzyme.upper(), phase=phase) for phase in ("dense", "dilute") for enzyme in ("pt", "oc", "dmt")],
    ]
    if include_degradation:
        requirements.extend(_requirement(f"kdeg_{species}", "degradation_rate", species_id=species) for species in ("9", "10", "11", "13", "15"))
    return requirements


def m4_kinetic_requirements(*, include_degradation: bool = False) -> list[ParameterRequirement]:
    """M4-only requirements: M3 context is the sole source of phi/enzyme abundance/Kp."""
    m3_names = {item.name for item in m3_requirements()}
    return [item for item in m4_requirements(include_degradation=include_degradation) if item.name not in m3_names]


def requirement_name_to_kernel_key(name: str) -> str:
    """Explicit bridge between public requirement names and ODE constructor keys."""
    mapping = {f"partition_x{species}": f"partition_{species}" for species in ("9", "10", "11")}
    return mapping.get(name, name)


def recruitment_requirements(recruitment: object, *, binding_model: str) -> list[ParameterRequirement]:
    enzyme = recruitment.enzyme_id
    requirements = [
        _requirement(recruitment.enzyme_total_parameter, "abundance", enzyme_id=enzyme).model_copy(update={"blocking": False}),
        _requirement(recruitment.site_total_parameter, "abundance").model_copy(update={"blocking": False}),
        _requirement(recruitment.kd_parameter, "kd", enzyme_id=enzyme).model_copy(update={"blocking": False}),
    ]
    if binding_model == "hill" and recruitment.hill_coefficient_parameter:
        requirements.append(_requirement(recruitment.hill_coefficient_parameter, "hill_coefficient", enzyme_id=enzyme).model_copy(update={"blocking": False}))
    return requirements


def requirements_for_stage(project: object, stage: str, *, include_auxiliary: bool = True) -> list[ParameterRequirement]:
    """Project-aware, single catalog used by every production entry point."""
    if stage == "m3":
        core = m3_requirements()
        auxiliary = [item for recruitment in getattr(project.stages.m3_concentration, "recruitment", []) for item in recruitment_requirements(recruitment, binding_model=project.stages.m3_concentration.binding_model)]
        return core + auxiliary if include_auxiliary else core
    if stage == "m4":
        return m4_requirements(include_degradation=project.stages.m4_reaction.enable_degradation)
    return []
