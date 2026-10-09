"""M3 S1--S5 and E1--E9 implementation with explicit mass conservation."""

from __future__ import annotations

from typing import Literal
from math import exp, isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import brentq


M3_FORMULA_VERSION = "m3-s1-e10-2026-09-27"
AVOGADRO_PER_MOL = 6.02214076e23
UM_NM3_TO_MOLECULE_FRACTION = 1e-30 * AVOGADRO_PER_MOL


class AvidityCorrection(BaseModel):
    """Optional source-proposed Kd correction; no factor is inferred from geometry."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    method: Literal["statistical_factor", "alpha", "free_energy"]
    value: float | None = Field(default=None, gt=0)
    delta_delta_g_j_per_mol: float | None = Field(default=None, le=0)
    temperature_k: float | None = Field(default=None, gt=0)
    source_reference: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)
    parameter_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def selected_method(self):
        if self.method == "free_energy":
            if self.value is not None or self.delta_delta_g_j_per_mol is None or self.temperature_k is None:
                raise ValueError("free_energy_requires_delta_delta_G_and_temperature_only")
        elif self.value is None or self.delta_delta_g_j_per_mol is not None or self.temperature_k is not None:
            raise ValueError("avidity_factor_requires_only_explicit_positive_value")
        return self

    def kd_multiplier(self) -> float:
        if self.method == "statistical_factor":
            return 1/self.value
        if self.method == "alpha":
            return self.value
        factor = exp(self.delta_delta_g_j_per_mol/(8.31446261815324*self.temperature_k))
        if factor == 0:
            raise ValueError("avidity_exponential_underflow_no_zero_Kd_substitution")
        return factor


class M3EquilibriumInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    candidate_id: str
    construct_id: str
    formula_version: Literal["m3-s1-e10-2026-09-27"] = M3_FORMULA_VERSION
    compartment_scenario: Literal["cytosolic_two_phase"] = "cytosolic_two_phase"

    # S1: site counts and M2 geometry factors. The entity basis must match the
    # scaffold concentration basis so that no implicit 24-fold factor appears.
    s_sh3: int = Field(ge=0)
    s_pdz: int = Field(ge=0)
    eta_acc_sh3: float = Field(ge=0, le=1)
    eta_acc_pdz: float = Field(ge=0, le=1)
    eta_bind_sh3: float = Field(ge=0, le=1)
    eta_bind_pdz: float = Field(ge=0, le=1)
    site_count_basis: Literal["scaffold_monomer", "complete_assembly"]
    c_dense_basis: Literal["scaffold_monomer", "complete_assembly"]
    joint_occupancy_independent: bool = False
    m2_geometry_id: str

    # S4: use measured phi, the lever rule inputs, or both for an explicit
    # comparison. Concentrations use the canonical uM unit.
    phi: float | None = Field(default=None, ge=0, lt=1)
    c_scaffold_total_um: float | None = Field(default=None, ge=0)
    c_sat_um: float | None = Field(default=None, ge=0)
    c_dense_um: float = Field(gt=0)

    # E1--E6 physical inputs.
    kd_sh3_um: float = Field(gt=0)
    kd_pdz_um: float = Field(gt=0)
    k_oc: float = Field(gt=0)
    k_dmt: float = Field(gt=0)
    c_oc_total_um: float = Field(ge=0)
    c_dmt_total_um: float = Field(ge=0)

    # Optional S2/S3 capacity diagnostic. Both volumes must use nm^3 and must
    # be provided together. S3 intentionally retains the source's single
    # effective enzyme volume approximation.
    v_scaffold_nm3: float | None = Field(default=None, gt=0)
    v_enzyme_nm3: float | None = Field(default=None, gt=0)
    volume_method: str | None = None

    # Optional E8/E9 design target. These remain regime-conditional candidates.
    r_target: float | None = Field(default=None, gt=0)
    input_parameter_ids: list[str] = Field(min_length=1)
    avidity_sh3: AvidityCorrection | None = None
    avidity_pdz: AvidityCorrection | None = None

    @model_validator(mode="after")
    def _validate_contract(self) -> "M3EquilibriumInput":
        if self.site_count_basis != self.c_dense_basis:
            raise ValueError("site_count_basis_must_match_c_dense_basis")
        lever_values = (self.c_scaffold_total_um, self.c_sat_um)
        if self.phi is None and any(value is None for value in lever_values):
            raise ValueError("phi_or_complete_S4_lever_rule_inputs_required")
        if (self.c_scaffold_total_um is None) != (self.c_sat_um is None):
            raise ValueError("S4_requires_both_total_and_saturation_concentrations")
        if self.c_sat_um is not None and (self.c_dense_um <= self.c_sat_um or
                not self.c_sat_um <= self.c_scaffold_total_um < self.c_dense_um):
            raise ValueError("S4_requires_c_sat_le_total_lt_c_dense_and_positive_phase_gap")
        if (self.v_scaffold_nm3 is None) != (self.v_enzyme_nm3 is None):
            raise ValueError("S2_S3_capacity_requires_both_scaffold_and_enzyme_volumes")
        if self.v_scaffold_nm3 is not None and not self.volume_method:
            raise ValueError("capacity_volume_method_required")
        return self


class M3SpeciesResult(BaseModel):
    free_dense_um: float = Field(ge=0)
    free_dilute_um: float = Field(ge=0)
    bound_dense_um: float = Field(ge=0)
    total_dense_um: float = Field(ge=0)
    site_occupancy: float = Field(ge=0, le=1)
    site_unoccupied_fraction: float = Field(ge=0, le=1)
    bound_fraction_of_whole_cell_total: float = Field(ge=0, le=1)
    dense_phase_fraction_of_whole_cell_total: float = Field(ge=0, le=1)
    mass_balance_residual_um: float


class M3EquilibriumResult(BaseModel):
    candidate_id: str
    construct_id: str
    formula_version: Literal["m3-s1-e10-2026-09-27"] = M3_FORMULA_VERSION
    status: Literal["valid", "insufficient_data", "capacity_conflict"]
    m4_ready: bool
    phi: float = Field(ge=0, lt=1)
    phi_source: Literal["measured_input", "S4_lever_rule"]
    phi_s4_if_available: float | None = None
    n_sh3_effective: float = Field(ge=0)
    n_pdz_effective: float = Field(ge=0)
    recruitment_preference_b: float = Field(gt=0)
    effective_site_ratio_rho: float | None = Field(default=None, ge=0)
    oc: M3SpeciesResult | None = None
    dmt: M3SpeciesResult | None = None
    dense_oc_dmt_ratio: float | None = Field(default=None, ge=0)
    whole_cell_oc_dmt_ratio: float | None = Field(default=None, ge=0)
    free_dense_oc_dmt_ratio: float | None = Field(default=None, ge=0)
    e7_low_occupancy_dense_ratio_candidate: float | None = Field(default=None, ge=0)
    e7_free_ratio_candidate: float | None = Field(default=None, ge=0)
    excluded_volume_fraction: float | None = None
    maximum_dense_enzyme_concentration_um: float | None = None
    capacity_excess_um: float | None = None
    rho_star_low_occupancy_candidate: float | None = Field(default=None, ge=0)
    rho_star_saturation_candidate: float | None = Field(default=None, ge=0)
    normalized_sensitivities_e10: dict[str, float] = Field(default_factory=dict)
    input_parameter_ids: list[str]
    m2_geometry_id: str
    warnings: list[str] = Field(default_factory=list)
    avidity_corrections: dict = Field(default_factory=dict)


def solve_m3_equilibrium(payload: M3EquilibriumInput) -> M3EquilibriumResult:
    """Solve S1--S5 and E1--E6; report rather than patch capacity conflicts."""

    corrections = {}
    corrected = {}
    for domain in ("sh3", "pdz"):
        correction = getattr(payload, "avidity_"+domain)
        if correction is not None:
            kd_name = "kd_"+domain+"_um"
            corrected[kd_name] = getattr(payload, kd_name)*correction.kd_multiplier()
            if not isfinite(corrected[kd_name]) or corrected[kd_name] <= 0:
                raise ValueError("effective_avidity_Kd_outside_positive_finite_numeric_domain")
            corrections[domain] = {"unmodified_kd_um": getattr(payload, kd_name),
                "effective_kd_um": corrected[kd_name], "evidence": correction.model_dump(mode="json")}
    if corrected:
        payload = payload.model_copy(update={**corrected, "input_parameter_ids": sorted({*payload.input_parameter_ids,
            *(p for domain in ("sh3", "pdz") if getattr(payload, "avidity_"+domain) is not None
              for p in getattr(payload, "avidity_"+domain).parameter_ids)})})
    phi_s4 = _lever_rule_phi(payload)
    phi = payload.phi if payload.phi is not None else phi_s4
    assert phi is not None
    if not 0 <= phi < 1:
        raise ValueError("S4_phi_must_satisfy_0_le_phi_lt_1")

    n_sh3 = payload.s_sh3 * payload.eta_acc_sh3 * payload.eta_bind_sh3
    n_pdz = payload.s_pdz * payload.eta_acc_pdz * payload.eta_bind_pdz
    preference_b = payload.kd_sh3_um / payload.kd_pdz_um
    warnings: list[str] = []
    if phi_s4 is not None and payload.phi is not None and abs(phi_s4 - payload.phi) > 1e-9:
        warnings.append("measured_phi_and_S4_phi_differ_no_value_was_silently_replaced")
    if not payload.joint_occupancy_independent:
        return M3EquilibriumResult(
            candidate_id=payload.candidate_id,
            construct_id=payload.construct_id,
            status="insufficient_data",
            m4_ready=False,
            phi=phi,
            phi_source="measured_input" if payload.phi is not None else "S4_lever_rule",
            phi_s4_if_available=phi_s4,
            n_sh3_effective=n_sh3,
            n_pdz_effective=n_pdz,
            recruitment_preference_b=preference_b,
            effective_site_ratio_rho=n_sh3 / n_pdz if n_pdz > 0 else None,
            input_parameter_ids=payload.input_parameter_ids,
            m2_geometry_id=payload.m2_geometry_id,
            warnings=[*warnings, "M2_joint_occupancy_constraints_not_cleared_for_independent_E1_equations"],
            avidity_corrections=corrections,
        )

    oc = _solve_species(
        total=payload.c_oc_total_um,
        partition=payload.k_oc,
        kd=payload.kd_sh3_um,
        effective_sites=n_sh3,
        c_dense=payload.c_dense_um,
        phi=phi,
    )
    dmt = _solve_species(
        total=payload.c_dmt_total_um,
        partition=payload.k_dmt,
        kd=payload.kd_pdz_um,
        effective_sites=n_pdz,
        c_dense=payload.c_dense_um,
        phi=phi,
    )
    excluded_fraction = None
    maximum_dense = None
    capacity_excess = None
    status: Literal["valid", "insufficient_data", "capacity_conflict"] = "valid"
    if payload.v_scaffold_nm3 is not None and payload.v_enzyme_nm3 is not None:
        excluded_fraction = UM_NM3_TO_MOLECULE_FRACTION * payload.c_dense_um * payload.v_scaffold_nm3
        if excluded_fraction >= 1:
            status = "capacity_conflict"
            capacity_excess = oc.total_dense_um + dmt.total_dense_um
            warnings.append("S2_excluded_volume_fraction_is_at_least_one")
        else:
            maximum_dense = (1.0 - excluded_fraction) / (
                UM_NM3_TO_MOLECULE_FRACTION * payload.v_enzyme_nm3
            )
            capacity_excess = max(0.0, oc.total_dense_um + dmt.total_dense_um - maximum_dense)
            if capacity_excess > 1e-9:
                status = "capacity_conflict"
                warnings.append("S3_capacity_exceeded_no_nonconserving_proportional_rescaling_applied")

    ratio = oc.total_dense_um / dmt.total_dense_um if dmt.total_dense_um > 0 else None
    whole_ratio = payload.c_oc_total_um / payload.c_dmt_total_um if payload.c_dmt_total_um > 0 else None
    free_ratio = oc.free_dense_um / dmt.free_dense_um if dmt.free_dense_um > 0 else None
    rho = n_sh3 / n_pdz if n_pdz > 0 else None
    e7_dense = None
    e7_free = None
    if whole_ratio is not None and rho is not None:
        e7_dense = rho * whole_ratio * (payload.kd_pdz_um / payload.kd_sh3_um)
        e7_free = whole_ratio * (
            phi + (1.0 - phi) / payload.k_dmt
        ) / (
            phi + (1.0 - phi) / payload.k_oc
        )
        warnings.append("E7_values_are_low_occupancy_binding_dominated_candidates_not_full_model_equalities")
    rho_low = None
    rho_saturated = None
    if payload.r_target is not None and whole_ratio is not None and whole_ratio > 0:
        rho_low = (payload.r_target / whole_ratio) * (payload.kd_sh3_um / payload.kd_pdz_um)
        rho_saturated = payload.r_target
        warnings.append("rho_star_values_are_regime_conditional_E8_E9_candidates_not_global_optima")
    sensitivities = _normalized_sensitivities(payload, phi, n_sh3, n_pdz, oc, dmt)
    if not sensitivities:
        warnings.append("E10_sensitivities_unavailable_when_dense_ratio_is_undefined_or_zero")

    return M3EquilibriumResult(
        candidate_id=payload.candidate_id,
        construct_id=payload.construct_id,
        status=status,
        m4_ready=status == "valid",
        phi=phi,
        phi_source="measured_input" if payload.phi is not None else "S4_lever_rule",
        phi_s4_if_available=phi_s4,
        n_sh3_effective=n_sh3,
        n_pdz_effective=n_pdz,
        recruitment_preference_b=preference_b,
        effective_site_ratio_rho=rho,
        oc=oc,
        dmt=dmt,
        dense_oc_dmt_ratio=ratio,
        whole_cell_oc_dmt_ratio=whole_ratio,
        free_dense_oc_dmt_ratio=free_ratio,
        e7_low_occupancy_dense_ratio_candidate=e7_dense,
        e7_free_ratio_candidate=e7_free,
        excluded_volume_fraction=excluded_fraction,
        maximum_dense_enzyme_concentration_um=maximum_dense,
        capacity_excess_um=capacity_excess,
        rho_star_low_occupancy_candidate=rho_low,
        rho_star_saturation_candidate=rho_saturated,
        normalized_sensitivities_e10=sensitivities,
        input_parameter_ids=payload.input_parameter_ids,
        m2_geometry_id=payload.m2_geometry_id,
        warnings=warnings,
        avidity_corrections=corrections,
    )


def _lever_rule_phi(payload: M3EquilibriumInput) -> float | None:
    if payload.c_scaffold_total_um is None or payload.c_sat_um is None:
        return None
    denominator = payload.c_dense_um - payload.c_sat_um
    if denominator == 0:
        raise ValueError("S4_denominator_c_dense_minus_c_sat_must_not_be_zero")
    return (payload.c_scaffold_total_um - payload.c_sat_um) / denominator


def _solve_species(
    *,
    total: float,
    partition: float,
    kd: float,
    effective_sites: float,
    c_dense: float,
    phi: float,
) -> M3SpeciesResult:
    if total == 0:
        return M3SpeciesResult(
            free_dense_um=0.0,
            free_dilute_um=0.0,
            bound_dense_um=0.0,
            total_dense_um=0.0,
            site_occupancy=0.0,
            site_unoccupied_fraction=1.0,
            bound_fraction_of_whole_cell_total=0.0,
            dense_phase_fraction_of_whole_cell_total=0.0,
            mass_balance_residual_um=0.0,
        )

    def residual(free_dense: float) -> float:
        theta = free_dense / (kd + free_dense)
        bound_dense = theta * effective_sites * c_dense
        return phi * (free_dense + bound_dense) + (1.0 - phi) * (free_dense / partition) - total

    upper = max(total * partition / max(1.0 - phi, 1e-12), total, kd, 1.0)
    while residual(upper) < 0:
        upper *= 2.0
    free_dense = float(brentq(residual, 0.0, upper, xtol=1e-12, rtol=1e-12))
    theta = free_dense / (kd + free_dense)
    bound_dense = theta * effective_sites * c_dense
    total_dense = free_dense + bound_dense
    free_dilute = free_dense / partition
    balance = phi * total_dense + (1.0 - phi) * free_dilute
    return M3SpeciesResult(
        free_dense_um=free_dense,
        free_dilute_um=free_dilute,
        bound_dense_um=bound_dense,
        total_dense_um=total_dense,
        site_occupancy=theta,
        site_unoccupied_fraction=1.0 - theta,
        bound_fraction_of_whole_cell_total=phi * bound_dense / total,
        dense_phase_fraction_of_whole_cell_total=phi * total_dense / total,
        mass_balance_residual_um=balance - total,
    )


def _normalized_sensitivities(
    payload: M3EquilibriumInput,
    phi: float,
    n_sh3: float,
    n_pdz: float,
    oc: M3SpeciesResult,
    dmt: M3SpeciesResult,
) -> dict[str, float]:
    """Evaluate E10 analytically for the primitive conservative model inputs."""

    z_oc = oc.total_dense_um
    z_dmt = dmt.total_dense_um
    if z_oc <= 0 or z_dmt <= 0:
        return {}
    derivatives_oc = _dense_total_derivatives(
        free_dense=oc.free_dense_um,
        kd=payload.kd_sh3_um,
        effective_sites=n_sh3,
        c_dense=payload.c_dense_um,
        partition=payload.k_oc,
        phi=phi,
    )
    derivatives_dmt = _dense_total_derivatives(
        free_dense=dmt.free_dense_um,
        kd=payload.kd_pdz_um,
        effective_sites=n_pdz,
        c_dense=payload.c_dense_um,
        partition=payload.k_dmt,
        phi=phi,
    )

    def oc_only(value: float, derivative: float) -> float:
        return value * derivative / z_oc

    def dmt_only(value: float, derivative: float) -> float:
        return -value * derivative / z_dmt

    shared_phi = phi * (
        derivatives_oc["phi"] / z_oc - derivatives_dmt["phi"] / z_dmt
    )
    shared_dense = payload.c_dense_um * (
        derivatives_oc["c_dense"] / z_oc - derivatives_dmt["c_dense"] / z_dmt
    )
    result = {
        "kd_sh3": oc_only(payload.kd_sh3_um, derivatives_oc["kd"]),
        "kd_pdz": dmt_only(payload.kd_pdz_um, derivatives_dmt["kd"]),
        "n_sh3_effective": oc_only(n_sh3, derivatives_oc["effective_sites"]),
        "n_pdz_effective": dmt_only(n_pdz, derivatives_dmt["effective_sites"]),
        "phi": shared_phi,
        "c_dense_scaffold": shared_dense,
        "k_oc": oc_only(payload.k_oc, derivatives_oc["partition"]),
        "k_dmt": dmt_only(payload.k_dmt, derivatives_dmt["partition"]),
        "c_oc_total": oc_only(payload.c_oc_total_um, derivatives_oc["total"]),
        "c_dmt_total": dmt_only(payload.c_dmt_total_um, derivatives_dmt["total"]),
    }
    # Since n = s * eta_acc * eta_bind, the normalized sensitivities of each
    # nonzero multiplicative factor equal the normalized sensitivity to n.
    result["eta_acc_sh3"] = result["n_sh3_effective"] if payload.eta_acc_sh3 > 0 else 0.0
    result["eta_bind_sh3"] = result["n_sh3_effective"] if payload.eta_bind_sh3 > 0 else 0.0
    result["eta_acc_pdz"] = result["n_pdz_effective"] if payload.eta_acc_pdz > 0 else 0.0
    result["eta_bind_pdz"] = result["n_pdz_effective"] if payload.eta_bind_pdz > 0 else 0.0
    return result


def _dense_total_derivatives(
    *,
    free_dense: float,
    kd: float,
    effective_sites: float,
    c_dense: float,
    partition: float,
    phi: float,
) -> dict[str, float]:
    theta = free_dense / (kd + free_dense)
    bound_dense = effective_sites * c_dense * theta
    dz_dx = 1.0 + effective_sites * c_dense * kd / (kd + free_dense) ** 2
    d_f_dx = phi * dz_dx + (1.0 - phi) / partition

    partial_bound_dn = c_dense * theta
    partial_bound_dc = effective_sites * theta
    partial_bound_dkd = -effective_sites * c_dense * free_dense / (kd + free_dense) ** 2
    dx_dn = -phi * partial_bound_dn / d_f_dx
    dx_dc = -phi * partial_bound_dc / d_f_dx
    dx_dkd = -phi * partial_bound_dkd / d_f_dx
    dx_dpartition = (1.0 - phi) * free_dense / (partition**2 * d_f_dx)
    dx_dtotal = 1.0 / d_f_dx
    dx_dphi = -((free_dense + bound_dense) - free_dense / partition) / d_f_dx
    return {
        "effective_sites": dz_dx * dx_dn + partial_bound_dn,
        "c_dense": dz_dx * dx_dc + partial_bound_dc,
        "kd": dz_dx * dx_dkd + partial_bound_dkd,
        "partition": dz_dx * dx_dpartition,
        "total": dz_dx * dx_dtotal,
        "phi": dz_dx * dx_dphi,
    }
