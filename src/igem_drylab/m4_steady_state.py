"""M4 documented ten-reaction, two-phase competitive steady-state model."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import least_squares

from .full_network import (
    COMPOUNDS,
    ENZYME_SUBSTRATES,
    REACTIONS,
    PhaseDistribution,
    ReactionKinetics,
    phase_competitive_rates,
    phase_partition,
)


M4_FORMULA_VERSION = "m4-step0-step8-2026-09-27"
M4_ACTIVITY_FORMULA_VERSION = "m4-step0-step8-phase-activity-v2-2026-10-04"


class M4ReactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    reaction_id: str
    enzyme: Literal["PTR", "PT", "OC", "DMT"]
    substrate: str
    product: str
    kcat_per_h: float = Field(ge=0)
    km_um: float = Field(gt=0)
    parameter_ids: list[str] = Field(min_length=2)


class M4PhaseEnzymeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    dense_um: float = Field(ge=0)
    dilute_um: float = Field(ge=0)
    m3_source_id: str
    activity_dense_ratio: float = Field(default=1.0, ge=0)
    activity_dilute_ratio: float = Field(default=1.0, ge=0)


class M4SteadyStateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    candidate_id: str
    construct_id: str
    condition_id: str
    formula_version: Literal["m4-step0-step8-2026-09-27", "m4-step0-step8-phase-activity-v2-2026-10-04"] = M4_FORMULA_VERSION
    phi: float = Field(ge=0, lt=1)
    enzymes: dict[str, M4PhaseEnzymeInput]
    metabolite_kp: dict[str, float]
    reactions: list[M4ReactionInput]
    input_flux_um_per_h: float = Field(gt=0)
    secretion_rate_per_h: dict[str, float]
    secretion_normalization: Literal["original_unweighted_dilute_concentration"]
    initial_guess_um: dict[str, float]
    input_parameter_ids: list[str] = Field(min_length=1)
    residual_tolerance_um_per_h: float = Field(default=1e-8, gt=0)
    relative_residual_tolerance: float = Field(default=1e-6, gt=0, lt=1)

    @model_validator(mode="after")
    def _validate_complete_network(self) -> "M4SteadyStateInput":
        if any(item.activity_dense_ratio != 1 or item.activity_dilute_ratio != 1 for item in self.enzymes.values()):
            self.formula_version = M4_ACTIVITY_FORMULA_VERSION
        if set(self.enzymes) != set(ENZYME_SUBSTRATES):
            raise ValueError("M4_requires_PTR_PT_OC_DMT_phase_concentrations")
        if set(self.metabolite_kp) != set(COMPOUNDS) or any(value <= 0 for value in self.metabolite_kp.values()):
            raise ValueError("M4_requires_positive_Kp_for_compounds_8_to_15")
        if set(self.secretion_rate_per_h) != set(COMPOUNDS) or any(value < 0 for value in self.secretion_rate_per_h.values()):
            raise ValueError("M4_requires_nonnegative_ksec_for_compounds_8_to_15")
        if set(self.initial_guess_um) != set(COMPOUNDS) or any(value < 0 for value in self.initial_guess_um.values()):
            raise ValueError("M4_requires_nonnegative_initial_guess_for_compounds_8_to_15")
        identities = tuple((item.reaction_id, item.enzyme, item.substrate, item.product) for item in self.reactions)
        if identities != REACTIONS:
            raise ValueError("M4_requires_canonical_R1_to_R10_network_R10_is_14_to_15")
        return self


class M4SteadyStateResult(BaseModel):
    candidate_id: str
    construct_id: str
    condition_id: str
    formula_version: Literal["m4-step0-step8-2026-09-27", "m4-step0-step8-phase-activity-v2-2026-10-04"] = M4_FORMULA_VERSION
    status: Literal["valid", "blocked", "solver_failed"]
    concentrations_cell_average_um: dict[str, float] = Field(default_factory=dict)
    concentrations_dense_um: dict[str, float] = Field(default_factory=dict)
    concentrations_dilute_um: dict[str, float] = Field(default_factory=dict)
    reaction_flux_um_per_h: dict[str, float] = Field(default_factory=dict)
    secretion_flux_um_per_h: dict[str, float] = Field(default_factory=dict)
    steady_state_residual_um_per_h: dict[str, float] = Field(default_factory=dict)
    yield_abs: float | None = Field(default=None, ge=0)
    secretion_loss_8_to_14: float | None = Field(default=None, ge=0)
    mass_invariant_residual: float | None = None
    max_scaled_species_residual: float | None = None
    input_output_balance_relative_residual: float | None = None
    robustness: None = None
    sensitivity: None = None
    scaffold_scan: None = None
    input_parameter_ids: list[str]
    warnings: list[str] = Field(default_factory=list)


def load_m4_reaction_identities(path: Path) -> tuple[tuple[str, str, str, str], ...]:
    """Read only the canonical identity fields required by the steady-state model."""

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"reaction_id", "enzyme", "substrate", "product"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("M4_reaction_network_requires_identity_columns")
    identities = tuple(
        (row["reaction_id"], row["enzyme"], row["substrate"], row["product"])
        for row in rows
    )
    if identities != REACTIONS:
        raise ValueError("M4_requires_canonical_R1_to_R10_network_R10_is_14_to_15")
    return identities


def solve_m4_steady_state(payload: M4SteadyStateInput) -> M4SteadyStateResult:
    """Solve the eight original steady-state balances without dynamic substitution."""

    if payload.secretion_rate_per_h["15"] <= 0:
        return _blocked(payload, "nonzero_M15_steady_state_requires_ksec_15_or_another_declared_M15_outlet")
    reactions = tuple(
        ReactionKinetics(
            item.reaction_id,
            item.enzyme,
            item.substrate,
            item.product,
            item.kcat_per_h,
            item.km_um,
        )
        for item in payload.reactions
    )
    enzymes = {
        name: PhaseDistribution(item.dense_um, item.dilute_um)
        for name, item in payload.enzymes.items()
    }
    active_edges = [(item.substrate,item.product) for item in payload.reactions if item.kcat_per_h > 0 and
                    (payload.phi*payload.enzymes[item.enzyme].dense_um*payload.enzymes[item.enzyme].activity_dense_ratio +
                     (1-payload.phi)*payload.enzymes[item.enzyme].dilute_um*payload.enzymes[item.enzyme].activity_dilute_ratio) > 0]
    drains = {c for c in COMPOUNDS if payload.secretion_rate_per_h[c] > 0}
    while True:
        expanded = drains | {a for a,b in active_edges if b in drains}
        if expanded == drains:
            break
        drains = expanded
    if "8" not in drains:
        return _blocked(payload, "positive_input_has_no_reachable_declared_outlet")

    def evaluate(cell_average: np.ndarray) -> tuple[np.ndarray, dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
        dense: dict[str, float] = {}
        dilute: dict[str, float] = {}
        for index, compound in enumerate(COMPOUNDS):
            phases = phase_partition(float(cell_average[index]), payload.metabolite_kp[compound], payload.phi)
            dense[compound], dilute[compound] = phases.dense, phases.dilute
        dense_rates = phase_competitive_rates(dense, {name: item.dense for name, item in enzymes.items()}, reactions, {name: item.activity_dense_ratio for name, item in payload.enzymes.items()}, 1.0)
        dilute_rates = phase_competitive_rates(dilute, {name: item.dilute for name, item in enzymes.items()}, reactions, {name: item.activity_dilute_ratio for name, item in payload.enzymes.items()}, 1.0)
        flux = {
            reaction_id: payload.phi * dense_rates[reaction_id] + (1.0 - payload.phi) * dilute_rates[reaction_id]
            for reaction_id, *_ in REACTIONS
        }
        secretion = {
            compound: payload.secretion_rate_per_h[compound] * dilute[compound]
            for compound in COMPOUNDS
        }
        residual = np.zeros(8, dtype=float)
        residual[0] += payload.input_flux_um_per_h
        index_by_compound = {compound: index for index, compound in enumerate(COMPOUNDS)}
        for reaction_id, _enzyme, substrate, product in REACTIONS:
            residual[index_by_compound[substrate]] -= flux[reaction_id]
            residual[index_by_compound[product]] += flux[reaction_id]
        for index, compound in enumerate(COMPOUNDS):
            residual[index] -= secretion[compound]
        return residual, flux, secretion, dense, dilute

    initial = np.asarray([payload.initial_guess_um[compound] for compound in COMPOUNDS], dtype=float)
    solved = least_squares(
        lambda values: evaluate(values)[0] / payload.input_flux_um_per_h,
        initial,
        bounds=(np.zeros(8), np.full(8, np.inf)),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=20_000,
    )
    residual, flux, secretion, dense, dilute = evaluate(solved.x)
    maximum_residual = float(np.max(np.abs(residual)))
    scaled_residual = maximum_residual / payload.input_flux_um_per_h
    production_15 = flux["R7"] + flux["R10"]
    yield_abs = production_15 / payload.input_flux_um_per_h
    secretion_loss = sum(secretion[str(index)] for index in range(8, 15)) / payload.input_flux_um_per_h
    invariant = yield_abs + secretion_loss - 1.0
    global_balance = sum(secretion.values()) / payload.input_flux_um_per_h - 1.0
    finite = np.all(np.isfinite(solved.x)) and np.all(np.isfinite(residual)) and all(np.isfinite(v) for v in [*flux.values(),*secretion.values(),invariant,global_balance])
    if (not solved.success or not finite or scaled_residual > payload.relative_residual_tolerance or
            maximum_residual > max(payload.residual_tolerance_um_per_h,payload.relative_residual_tolerance*payload.input_flux_um_per_h) or
            abs(invariant) > payload.relative_residual_tolerance or abs(global_balance) > payload.relative_residual_tolerance):
        return M4SteadyStateResult(
            candidate_id=payload.candidate_id,
            construct_id=payload.construct_id,
            condition_id=payload.condition_id,
            status="solver_failed",
            formula_version=payload.formula_version,
            concentrations_cell_average_um={compound: float(solved.x[index]) for index, compound in enumerate(COMPOUNDS)},
            steady_state_residual_um_per_h={compound: float(residual[index]) for index, compound in enumerate(COMPOUNDS)},
            input_parameter_ids=payload.input_parameter_ids,
            mass_invariant_residual=float(invariant) if np.isfinite(invariant) else None,
            max_scaled_species_residual=float(scaled_residual) if np.isfinite(scaled_residual) else None,
            input_output_balance_relative_residual=float(global_balance) if np.isfinite(global_balance) else None,
            warnings=[f"steady_state_solver_failed_or_residual_exceeded_tolerance:{solved.message}"],
        )
    return M4SteadyStateResult(
        candidate_id=payload.candidate_id,
        construct_id=payload.construct_id,
        condition_id=payload.condition_id,
        status="valid",
        formula_version=payload.formula_version,
        concentrations_cell_average_um={compound: float(solved.x[index]) for index, compound in enumerate(COMPOUNDS)},
        concentrations_dense_um=dense,
        concentrations_dilute_um=dilute,
        reaction_flux_um_per_h=flux,
        secretion_flux_um_per_h=secretion,
        steady_state_residual_um_per_h={compound: float(residual[index]) for index, compound in enumerate(COMPOUNDS)},
        yield_abs=yield_abs,
        secretion_loss_8_to_14=secretion_loss,
        mass_invariant_residual=invariant,
        max_scaled_species_residual=scaled_residual,
        input_output_balance_relative_residual=global_balance,
        input_parameter_ids=payload.input_parameter_ids,
        warnings=[
            "R10_substrate_corrected_to_M14_per_canonical_reaction_table",
            "Vsec_uses_original_unweighted_ksec_times_dilute_concentration_definition",
            "robustness_sensitivity_and_scaffold_scan_withheld_without_reviewed_distributions_or_constructs",
            "valid_means_balanced_numerical_root_not_stability_or_uniqueness_validation",
        ],
    )


def _blocked(payload: M4SteadyStateInput, reason: str) -> M4SteadyStateResult:
    return M4SteadyStateResult(
        candidate_id=payload.candidate_id,
        construct_id=payload.construct_id,
        condition_id=payload.condition_id,
        status="blocked",
        formula_version=payload.formula_version,
        input_parameter_ids=payload.input_parameter_ids,
        warnings=[reason],
    )
