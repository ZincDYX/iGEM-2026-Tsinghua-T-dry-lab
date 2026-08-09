"""Two-compartment enrichment calculations with mass conservation.

This module models a cytosol/condensate abstraction. Partition coefficients are
inputs, not inferred from structure confidence, linker sequence, or docking.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .kinetics import phase_concentrations
from .multichain import solve_binding_equilibrium
from .parameters.models import ParameterUncertainty


class EnrichmentInput(BaseModel):
    species_id: str
    total_concentration: float = Field(ge=0)
    partition_coefficient: float = Field(gt=0)
    partition_source: str
    partition_uncertainty: ParameterUncertainty | None = None


class EnrichmentResult(BaseModel):
    species_id: str
    dense_concentration: float = Field(ge=0)
    dilute_concentration: float = Field(ge=0)
    fraction_in_dense: float = Field(ge=0, le=1)
    partition_coefficient: float = Field(gt=0)
    phi: float = Field(ge=0, le=1)
    provenance: str
    partition_uncertainty: ParameterUncertainty | None = None


class RecruitmentInput(BaseModel):
    enzyme_id: str
    enzyme_total: float = Field(ge=0)
    site_total: float = Field(ge=0)
    kd: float = Field(gt=0)
    binding_model: str = "independent"
    hill_coefficient: float | None = Field(default=None, gt=0)


class RecruitmentResult(BaseModel):
    enzyme_id: str
    recruited_fraction: float = Field(ge=0, le=1)
    site_occupancy: float = Field(ge=0, le=1)
    model: str
    notes: str


def calculate_enrichment(item: EnrichmentInput, *, phi: float) -> EnrichmentResult:
    """Calculate dense/dilute concentration and recruited fraction.

    Assumes rapid equilibrium and a single condensate phase volume fraction
    ``phi``. It does not establish that a condensate exists or that a supplied
    Kp applies in vivo.
    """
    if not 0 <= phi <= 1:
        raise ValueError("phi must be between 0 and 1")
    dense, dilute = phase_concentrations(item.total_concentration, item.partition_coefficient, phi)
    fraction = phi * dense / item.total_concentration if item.total_concentration else 0.0
    return EnrichmentResult(
        species_id=item.species_id, dense_concentration=dense, dilute_concentration=dilute,
        fraction_in_dense=fraction, partition_coefficient=item.partition_coefficient, phi=phi,
        provenance=item.partition_source, partition_uncertainty=item.partition_uncertainty,
    )


def calculate_many(items: list[EnrichmentInput], *, phi: float) -> dict[str, EnrichmentResult]:
    """Calculate independent species partitioning, rejecting duplicate species IDs."""
    if len({item.species_id for item in items}) != len(items):
        raise ValueError("species IDs must be unique")
    return {item.species_id: calculate_enrichment(item, phi=phi) for item in items}


def calculate_recruitment(item: RecruitmentInput) -> RecruitmentResult:
    """Calculate finite-site recruitment using independent or explicit Hill mode.

    Hill cooperativity is never inferred: ``hill_coefficient`` is mandatory for
    hill mode. This result describes tag/site binding, not LLPS formation.
    """
    if item.binding_model == "independent":
        equilibrium = solve_binding_equilibrium(receptor="site", ligand=item.enzyme_id, receptor_total=item.site_total, ligand_total=item.enzyme_total, kd=item.kd)
        return RecruitmentResult(enzyme_id=item.enzyme_id, recruited_fraction=equilibrium.bound_site_concentration / item.enzyme_total if item.enzyme_total else 0.0, site_occupancy=equilibrium.receptor_site_occupancy, model="independent", notes="finite-site equilibrium")
    if item.binding_model == "hill":
        if item.hill_coefficient is None: raise ValueError("hill_coefficient is required for hill binding")
        fraction = item.enzyme_total ** item.hill_coefficient / (item.kd ** item.hill_coefficient + item.enzyme_total ** item.hill_coefficient) if item.enzyme_total else 0.0
        return RecruitmentResult(enzyme_id=item.enzyme_id, recruited_fraction=fraction, site_occupancy=min(1.0, item.enzyme_total * fraction / item.site_total) if item.site_total else 0.0, model="hill", notes="phenomenological Hill input")
    raise ValueError("binding_model must be independent or hill")
