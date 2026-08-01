from __future__ import annotations

import math

from .models import BindingEquilibriumResult


def solve_binding_equilibrium(
    *,
    receptor: str,
    ligand: str,
    receptor_total: float,
    ligand_total: float,
    kd: float,
    receptor_valency: int = 1,
    ligand_valency: int = 1,
) -> BindingEquilibriumResult:
    """Solve a finite-site A + B <-> AB binding equilibrium.

    Concentrations and Kd must use the same unit. Valency is represented as
    site count per molecule, which is the minimal useful model for iLID/SspB,
    SH3/ligand, PDZ/ligand, and similar engineered recruitment pairs.
    """
    if receptor_total < 0 or ligand_total < 0:
        raise ValueError("Total concentrations must be non-negative")
    if kd <= 0:
        raise ValueError("Kd must be positive")
    if receptor_valency < 1 or ligand_valency < 1:
        raise ValueError("Valencies must be positive integers")

    receptor_sites = receptor_total * receptor_valency
    ligand_sites = ligand_total * ligand_valency
    bound_sites = _solve_one_to_one_bound_sites(receptor_sites, ligand_sites, kd)
    receptor_occupancy = _safe_fraction(bound_sites, receptor_sites)
    ligand_occupancy = _safe_fraction(bound_sites, ligand_sites)
    limiting = receptor if receptor_sites <= ligand_sites else ligand
    return BindingEquilibriumResult(
        ligand=ligand,
        receptor=receptor,
        kd=kd,
        receptor_total=receptor_total,
        ligand_total=ligand_total,
        receptor_valency=receptor_valency,
        ligand_valency=ligand_valency,
        receptor_site_total=receptor_sites,
        ligand_site_total=ligand_sites,
        bound_site_concentration=bound_sites,
        receptor_site_occupancy=receptor_occupancy,
        ligand_site_occupancy=ligand_occupancy,
        limiting_component=limiting,
    )


def _solve_one_to_one_bound_sites(a_total: float, b_total: float, kd: float) -> float:
    if a_total == 0 or b_total == 0:
        return 0.0
    term = a_total + b_total + kd
    discriminant = max(0.0, term * term - 4 * a_total * b_total)
    return 0.5 * (term - math.sqrt(discriminant))


def _safe_fraction(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))
