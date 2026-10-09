"""User-defined two-phase networks with an explicit supported rate law.

This is an additional model contract; it does not replace the original Galatea
Step 0–8 equations or its canonical reaction-identity checks.
"""
from __future__ import annotations

import numpy as np
from pydantic import Field, model_validator

from .models import Contract


class PhaseEnzyme(Contract):
    dense_um: float = Field(ge=0)
    dilute_um: float = Field(ge=0)
    source: str = Field(min_length=1)


class Reaction(Contract):
    id: str
    enzyme: str
    substrate: str
    stoichiometry: dict[str, float]
    kcat_per_h: float = Field(ge=0)
    km_um: float = Field(gt=0)
    parameter_source: str = Field(min_length=1)


class Pathway(Contract):
    id: str
    rate_law: str = "two_phase_competitive_mm_v1"
    concentration_unit: str = "uM"
    time_unit: str = "h"
    secretion_definition: str = "unweighted_dilute_concentration"
    species: list[str] = Field(min_length=1)
    reactions: list[Reaction] = Field(min_length=1)
    enzymes: dict[str, PhaseEnzyme]
    phi: float = Field(ge=0, lt=1)
    partition_coefficients: dict[str, float]
    input_flux_um_per_h: dict[str, float]
    secretion_rate_per_h: dict[str, float]
    initial_guess_um: dict[str, float]
    residual_tolerance: float = Field(default=1e-8, gt=0)

    @model_validator(mode="after")
    def validate_network(self) -> "Pathway":
        if self.rate_law != "two_phase_competitive_mm_v1":
            raise ValueError("unsupported_rate_law")
        if (self.concentration_unit, self.time_unit) != ("uM", "h"):
            raise ValueError("pathway_requires_uM_and_h")
        if self.secretion_definition != "unweighted_dilute_concentration":
            raise ValueError("unsupported_secretion_definition")
        species = set(self.species)
        if len(species) != len(self.species):
            raise ValueError("duplicate_species")
        if len({reaction.id for reaction in self.reactions}) != len(self.reactions):
            raise ValueError("duplicate_reaction")
        for field_name in ("partition_coefficients", "input_flux_um_per_h", "secretion_rate_per_h", "initial_guess_um"):
            values = getattr(self, field_name)
            if set(values) != species or any(not np.isfinite(value) or value < 0 for value in values.values()):
                raise ValueError(f"complete_nonnegative_values_required:{field_name}")
        if any(value == 0 for value in self.partition_coefficients.values()):
            raise ValueError("positive_partition_coefficients_required")
        for reaction in self.reactions:
            if reaction.enzyme not in self.enzymes or reaction.substrate not in species or set(reaction.stoichiometry) - species:
                raise ValueError("unknown_reaction_entity")
            negatives = {key: value for key, value in reaction.stoichiometry.items() if value < 0}
            if negatives != {reaction.substrate: -1.0} or not any(value > 0 for value in reaction.stoichiometry.values()):
                raise ValueError("supported_MM_requires_one_substrate_with_coefficient_minus_one_and_products")
            if any(not np.isfinite(value) for value in reaction.stoichiometry.values()):
                raise ValueError("finite_stoichiometry_required")
        # One substrate may participate in multiple catalytic channels, but its
        # binding constant must be consistent within one enzyme competition pool.
        affinities: dict[tuple[str, str], float] = {}
        for reaction in self.reactions:
            key = (reaction.enzyme, reaction.substrate)
            if key in affinities and affinities[key] != reaction.km_um:
                raise ValueError("same_enzyme_substrate_requires_consistent_Km")
            affinities[key] = reaction.km_um
        return self


def solve_pathway(model: Pathway) -> dict[str, object]:
    from scipy.optimize import least_squares
    index = {name: position for position, name in enumerate(model.species)}
    matrix = np.zeros((len(model.species), len(model.reactions)))
    for column, reaction in enumerate(model.reactions):
        for species, coefficient in reaction.stoichiometry.items():
            matrix[index[species], column] = coefficient
    kp = np.array([model.partition_coefficients[name] for name in model.species])
    input_flux = np.array([model.input_flux_um_per_h[name] for name in model.species])
    ksec = np.array([model.secretion_rate_per_h[name] for name in model.species])
    pools: dict[str, dict[str, float]] = {}
    for reaction in model.reactions:
        pools.setdefault(reaction.enzyme, {})[reaction.substrate] = reaction.km_um

    def evaluate(average: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        dilute = average / ((1 - model.phi) + model.phi * kp)
        dense = kp * dilute if model.phi > 0 else np.zeros_like(dilute)
        flux = np.zeros(len(model.reactions))
        for volume, phase, dense_phase in ((model.phi, dense, True), (1 - model.phi, dilute, False)):
            denominators = {enzyme: 1 + sum(phase[index[substrate]] / km for substrate, km in substrates.items()) for enzyme, substrates in pools.items()}
            for position, reaction in enumerate(model.reactions):
                enzyme = model.enzymes[reaction.enzyme]
                abundance = enzyme.dense_um if dense_phase else enzyme.dilute_um
                flux[position] += volume * reaction.kcat_per_h * abundance * (phase[index[reaction.substrate]] / reaction.km_um) / denominators[reaction.enzyme]
        residual = input_flux + matrix @ flux - ksec * dilute
        return residual, flux, dense, dilute

    solution = least_squares(lambda values: evaluate(values)[0], [model.initial_guess_um[name] for name in model.species], bounds=(0, np.inf), xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=20_000)
    residual, flux, dense, dilute = evaluate(solution.x)
    valid = bool(solution.success and np.max(np.abs(residual)) <= model.residual_tolerance)
    return {
        "schema_version": "pathway-steady-state-v1", "model_kind": "generic_two_phase_steady_state",
        "status": "valid" if valid else "solver_failed", "pathway_id": model.id,
        "numerically_solved": valid,
        "evidence_ready": False,
        "claim_scope": "user_supplied_mechanistic_calculator",
        "evidence_status": "unreviewed_user_inputs",
        "rate_law": model.rate_law, "concentration_unit": "uM", "time_unit": "h",
        "concentrations_average_um": dict(zip(model.species, solution.x.tolist())),
        "concentrations_dense_um": dict(zip(model.species, dense.tolist())),
        "concentrations_dilute_um": dict(zip(model.species, dilute.tolist())),
        "reaction_flux_um_per_h": dict(zip([reaction.id for reaction in model.reactions], flux.tolist())),
        "secretion_flux_um_per_h": dict(zip(model.species, (ksec * dilute).tolist())),
        "residual_um_per_h": dict(zip(model.species, residual.tolist())),
        "solver_message": solution.message,
        "scope": "Explicit single-substrate competitive MM model; no inferred kinetic parameters or generalized yield definition.",
    }
