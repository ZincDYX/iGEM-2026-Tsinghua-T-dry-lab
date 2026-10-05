"""Single source of truth for the M3/M4 parameter contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Dimension = Literal["dimensionless", "concentration", "rate", "concentration_rate", "volume"]


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
    enzyme_sequence_sha256: str | None = None


def _requirement(name: str, parameter_type: str, **identity: str | None) -> ParameterRequirement:
    if parameter_type in {"phi", "kp", "activity_ratio", "hill_coefficient"}:
        minimum, inclusive = (0.0, True) if parameter_type in {"phi", "activity_ratio"} else (0.0, False)
        maximum = 1.0 if parameter_type == "phi" else None
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", minimum=minimum, minimum_inclusive=inclusive, maximum=maximum, **identity)
    if parameter_type in {"km", "kd", "abundance"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="concentration", canonical_unit="uM", minimum=0.0, minimum_inclusive=parameter_type == "abundance", **identity)
    if parameter_type in {"kcat", "degradation_rate", "export_rate"}:
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="rate", canonical_unit="1/h", minimum=0.0, **identity)
    if parameter_type == "input_flux":
        return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="concentration_rate", canonical_unit="uM/h", minimum=0.0, minimum_inclusive=False, **identity)
    return ParameterRequirement(name=name, parameter_type=parameter_type, dimension="dimensionless", **identity)


def m3_requirements() -> list[ParameterRequirement]:
    """Inputs for the documented M3 S1--S5/E1--E6 equilibrium."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"{enzyme}_total", "abundance", enzyme_id=enzyme.upper()) for enzyme in ("ptr", "pt", "oc", "dmt")],
        *[_requirement(f"partition_{species}", "kp", species_id=species.upper()) for species in ("ptr", "pt", "oc", "dmt")],
        _requirement("c_dense_scaffold", "abundance"),
        _requirement("kd_sh3", "kd"),
        _requirement("kd_pdz", "kd"),
    ]


def legacy_m3_independent_partition_requirements() -> list[ParameterRequirement]:
    """Historical partition-only mode retained only for explicit regressions."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"{enzyme}_total", "abundance", enzyme_id=enzyme.upper()) for enzyme in ("pt", "oc", "dmt")],
        *[_requirement(f"partition_{species}", "kp", species_id=species.upper()) for species in ("pt", "oc", "dmt")],
    ]


def m3_effective_ratio_requirements() -> list[ParameterRequirement]:
    """Requirements for the explicit Galatea engineering-ratio M3 mode."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"{enzyme}_total", "abundance", enzyme_id=enzyme.upper()) for enzyme in ("ptr", "pt", "oc", "dmt")],
        *[_requirement(f"partition_x{species}", "kp", species_id=species) for species in ("8", "9", "10", "11", "12", "13", "14", "15")],
    ]


def author_native_m3_effective_ratio_requirements() -> list[ParameterRequirement]:
    """Only dimensionless M3 values resolved from Registry in author-native mode."""
    return [
        _requirement("phi", "phi"),
        *[_requirement(f"partition_x{species}", "kp", species_id=species) for species in ("8", "9", "10", "11", "12", "13", "14", "15")],
    ]


def author_native_m4_sensitivity_requirements(*, include_activity: bool = False) -> list[ParameterRequirement]:
    """Author-native kinetics come from the cited reaction CSV, never Registry."""
    if not include_activity:
        return []
    return [
        _requirement(f"activity_{phase}_{enzyme.lower()}", "activity_ratio", enzyme_id=enzyme, phase=phase)
        for phase in ("dense", "dilute")
        for enzyme in ("PTR", "PT", "OC", "DMT")
    ]


def full_m4_kinetic_requirements(*, include_transport: bool = False, include_activity: bool = False) -> list[ParameterRequirement]:
    """Full ten-reaction kinetics; M3 owns phase partition and enzyme distributions."""
    mapping = (
        ("r1", "PTR", "8", "9"), ("r2", "PT", "9", "10"), ("r3", "OC", "10", "11"),
        ("r4", "DMT", "8", "12"), ("r5", "DMT", "9", "13"), ("r6", "DMT", "10", "14"),
        ("r7", "DMT", "11", "15"), ("r8", "PTR", "12", "13"), ("r9", "PT", "13", "14"),
        ("r10", "OC", "14", "15"),
    )
    requirements = [
        item
        for name, enzyme, substrate, product in mapping
        for item in (_requirement(f"kcat_{name}", "kcat", enzyme_id=enzyme, substrate_id=substrate, product_id=product), _requirement(f"km_{name}", "km", enzyme_id=enzyme, substrate_id=substrate))
    ]
    if include_activity:
        requirements.extend(_requirement(f"activity_{phase}_{enzyme.lower()}", "activity_ratio", enzyme_id=enzyme, phase=phase) for phase in ("dense", "dilute") for enzyme in ("PTR", "PT", "OC", "DMT"))
    if include_transport:
        requirements.append(_requirement("transport_rate", "export_rate"))
    return requirements


def m4_markdown_steady_requirements() -> list[ParameterRequirement]:
    return [
        *full_m4_kinetic_requirements(),
        _requirement("input_flux_8", "input_flux", species_id="8"),
        *[_requirement(f"ksec_{compound}", "export_rate", species_id=compound) for compound in ("8", "9", "10", "11", "12", "13", "14", "15")],
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


def _requirements_for_stage(project: object, stage: str, *, include_auxiliary: bool = True) -> list[ParameterRequirement]:
    """Project-aware, single catalog used by every production entry point."""
    if stage == "m3":
        author_native = getattr(project.stages.m4_reaction, "unit_mode", "physical") == "author_native_sensitivity"
        if getattr(project.stages.m3_concentration, "recruitment_mode", "finite_site") == "effective_ratio":
            return author_native_m3_effective_ratio_requirements() if author_native else m3_effective_ratio_requirements()
        mode = getattr(project.stages.m3_concentration, "recruitment_mode", "finite_site")
        core = legacy_m3_independent_partition_requirements() if mode == "legacy_independent_partition" else m3_requirements()
        settings = project.stages.m3_concentration
        if mode == "finite_site":
            if settings.phi_source == "lever_rule":
                core = [item for item in core if item.name != "phi"]
            if settings.phi_source in {"lever_rule", "compare"}:
                core += [_requirement("c_total_scaffold", "abundance"), _requirement("c_sat_scaffold", "abundance")]
            if settings.target_enzyme_ratio_parameter:
                core.append(ParameterRequirement(name=settings.target_enzyme_ratio_parameter, parameter_type="other",
                                                dimension="dimensionless", minimum=0., minimum_inclusive=False))
        if getattr(project.stages.m4_reaction, "network_mode", "legacy_reduced") in {"galatea_full_competitive", "markdown_steady_state"}:
            core = core + [_requirement(f"partition_x{species}", "kp", species_id=species) for species in ("8", "9", "10", "11", "12", "13", "14", "15")]
        auxiliary = [item for recruitment in getattr(project.stages.m3_concentration, "recruitment", []) for item in recruitment_requirements(recruitment, binding_model=project.stages.m3_concentration.binding_model)]
        return core + auxiliary if include_auxiliary else core
    if stage == "m4":
        m4 = project.stages.m4_reaction
        if getattr(m4, "network_mode", "legacy_reduced") == "markdown_steady_state":
            return [*m4_markdown_steady_requirements(), *(author_native_m4_sensitivity_requirements(include_activity=True) if m4.activity_mode == "sensitivity_parameters" else [])]
        if getattr(m4, "network_mode", "legacy_reduced") == "galatea_full_competitive":
            if m4.unit_mode == "author_native_sensitivity":
                return author_native_m4_sensitivity_requirements(include_activity=m4.activity_mode == "sensitivity_parameters")
            result = full_m4_kinetic_requirements(
                include_transport=m4.transport_enabled,
                include_activity=m4.activity_mode == "sensitivity_parameters",
            )
            if m4.transport_enabled and m4.transport_rate_parameter:
                result = [item.model_copy(update={"name": m4.transport_rate_parameter}) if item.name == "transport_rate" else item for item in result]
            return result
        return m4_requirements(include_degradation=project.stages.m4_reaction.enable_degradation)
    return []


def requirements_for_stage(project: object, stage: str, *, include_auxiliary: bool = True) -> list[ParameterRequirement]:
    inputs = getattr(project, "inputs", None)
    identities = {item.id: item.sequence_sha256 for item in inputs.enzymes} if inputs is not None else {}
    return [item.model_copy(update={"enzyme_sequence_sha256": identities.get(item.enzyme_id)})
            for item in _requirements_for_stage(project, stage, include_auxiliary=include_auxiliary)]
