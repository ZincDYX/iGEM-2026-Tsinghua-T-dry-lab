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
            if "formula_version" in self.model_fields_set and self.formula_version != M4_ACTIVITY_FORMULA_VERSION:
                raise ValueError("M4_phase_activity_requires_explicit_formula_version_migration")
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
    schema_version: Literal["m4-steady-state-v1"] = "m4-steady-state-v1"
    model_kind: Literal["markdown_steady_state"] = "markdown_steady_state"
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
    robustness: dict | None = None
    sensitivity: dict | None = None
    scaffold_scan: list[dict] | None = None
    input_parameter_ids: list[str]
    warnings: list[str] = Field(default_factory=list)
    local_stability: dict | None = None


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


def steady_state_evaluator(payload: M4SteadyStateInput):
    """One implementation of the original RHS, shared by solving and analysis."""
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

    return evaluate


def steady_state_jacobian(payload: M4SteadyStateInput, cell_average: np.ndarray) -> np.ndarray:
    """Exact derivative of the original competitive rates and unweighted Vsec."""
    dilute_factors = np.asarray([1 / (1 - payload.phi + payload.phi * payload.metabolite_kp[c]) for c in COMPOUNDS])
    dense_factors = dilute_factors * np.asarray([payload.metabolite_kp[c] for c in COMPOUNDS]) if payload.phi else np.zeros(8)
    index = {c: i for i, c in enumerate(COMPOUNDS)}
    jacobian = -np.diag([payload.secretion_rate_per_h[c] * dilute_factors[i] for i, c in enumerate(COMPOUNDS)])
    for phase, weight, factors in (("dense", payload.phi, dense_factors), ("dilute", 1-payload.phi, dilute_factors)):
        substrates = cell_average * factors
        for enzyme, concentration in payload.enzymes.items():
            entries = [r for r in payload.reactions if r.enzyme == enzyme]
            denominator = 1 + sum(substrates[index[r.substrate]] / r.km_um for r in entries)
            amount = getattr(concentration, phase+"_um") * getattr(concentration, "activity_"+phase+"_ratio")
            for reaction in entries:
                s = index[reaction.substrate]; p = index[reaction.product]
                numerator = substrates[s] / reaction.km_um
                for competitor in entries:
                    j = index[competitor.substrate]
                    derivative = weight * amount * reaction.kcat_per_h * factors[j] * (
                        (denominator / reaction.km_um if j == s else 0) - numerator / competitor.km_um
                    ) / denominator**2
                    jacobian[s, j] -= derivative
                    jacobian[p, j] += derivative
    return jacobian


def classify_local_stability(jacobian: np.ndarray, tolerance_per_h: float) -> dict:
    eigenvalues = np.linalg.eigvals(jacobian)
    largest = float(eigenvalues.real.max())
    status = "unstable" if largest > tolerance_per_h else (
        "locally_asymptotically_stable" if largest < -tolerance_per_h else "inconclusive_nonhyperbolic_or_numerically_neutral")
    return {"analysis_version": "original_rhs_analytic_jacobian_v1", "status": status,
        "jacobian_per_h": jacobian.tolist(), "eigenvalues_per_h": [{"real": float(v.real), "imag": float(v.imag)} for v in eigenvalues],
        "spectral_abscissa_per_h": largest, "numerical_eigenvalue_tolerance_per_h": tolerance_per_h,
        "scope": "local_linearization_not_global_stability_or_biological_validation"}


def solve_m4_steady_state(payload: M4SteadyStateInput) -> M4SteadyStateResult:
    """Solve the eight original steady-state balances without dynamic substitution."""
    if payload.secretion_rate_per_h["15"] <= 0:
        return _blocked(payload, "nonzero_M15_steady_state_requires_ksec_15_or_another_declared_M15_outlet")
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
    evaluate = steady_state_evaluator(payload)

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
        local_stability=classify_local_stability(steady_state_jacobian(payload, solved.x), 1e-10),
        warnings=[
            "R10_substrate_corrected_to_M14_per_canonical_reaction_table",
            "Vsec_uses_original_unweighted_ksec_times_dilute_concentration_definition",
            "robustness_sensitivity_and_scaffold_scan_withheld_without_reviewed_distributions_or_constructs",
            "valid_means_balanced_numerical_root_local_stability_is_separate_not_global_or_uniqueness_validation",
        ],
    )


class M4SteadyStateAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    steady_state_input: M4SteadyStateInput
    initial_guesses_um: list[dict[str, float]] = Field(min_length=1)
    root_merge_atol_um: float = Field(gt=0)
    root_merge_rtol: float = Field(gt=0, lt=1)
    eigenvalue_tolerance_per_h: float = Field(gt=0)

    @model_validator(mode="after")
    def _guesses(self):
        if any(set(guess) != set(COMPOUNDS) or any(v < 0 for v in guess.values()) for guess in self.initial_guesses_um):
            raise ValueError("analysis_initial_guesses_require_all_nonnegative_compounds")
        return self


def analyze_m4_steady_state(payload: M4SteadyStateAnalysisInput) -> dict:
    """Caller-declared multistart search; failures and root membership retained."""
    roots = []; attempts = []
    for guess in payload.initial_guesses_um:
        inputs = payload.steady_state_input.model_copy(update={"initial_guess_um": guess})
        result = solve_m4_steady_state(inputs)
        root_index = None
        if result.status == "valid":
            concentrations = np.asarray([result.concentrations_cell_average_um[c] for c in COMPOUNDS])
            result.local_stability = classify_local_stability(steady_state_jacobian(inputs, concentrations), payload.eigenvalue_tolerance_per_h)
            for i, root in enumerate(roots):
                other = np.asarray([root["concentrations_cell_average_um"][c] for c in COMPOUNDS])
                if np.all(np.abs(concentrations-other) <= payload.root_merge_atol_um + payload.root_merge_rtol*np.maximum(np.abs(concentrations), np.abs(other))):
                    root_index = i
                    break
            if root_index is None:
                root_index = len(roots)
                roots.append(result.model_dump(mode="json"))
        attempts.append({"initial_guess_um": guess, "root_index": root_index, "result": result.model_dump(mode="json")})
    return {"analysis_version": "declared_multistart_local_stability_v1", "roots": roots, "attempts": attempts,
        "distinct_roots_found": len(roots), "status": "roots_found" if roots else "no_valid_root_found",
        "settings": payload.model_dump(mode="json", exclude={"steady_state_input", "initial_guesses_um"}),
        "scope": "finite_initial_guess_search_not_global_uniqueness_or_nonexistence_proof"}


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
