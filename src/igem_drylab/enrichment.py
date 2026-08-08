"""Two-compartment enrichment calculations with mass conservation.

This module models a cytosol/condensate abstraction. Partition coefficients are
inputs, not inferred from structure confidence, linker sequence, or docking.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .kinetics import phase_concentrations


class EnrichmentInput(BaseModel):
    species_id: str
    total_concentration: float = Field(ge=0)
    partition_coefficient: float = Field(gt=0)
    partition_source: str
    activity_dense: float | None = Field(default=None, ge=0)
    activity_dilute: float | None = Field(default=None, ge=0)
    uncertainty: float | None = Field(default=None, ge=0)


class EnrichmentResult(BaseModel):
    species_id: str
    dense_concentration: float = Field(ge=0)
    dilute_concentration: float = Field(ge=0)
    fraction_in_dense: float = Field(ge=0, le=1)
    partition_coefficient: float = Field(gt=0)
    phi: float = Field(ge=0, le=1)
    provenance: str
    uncertainty: float | None = Field(default=None, ge=0)


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
        provenance=item.partition_source, uncertainty=item.uncertainty,
    )


def calculate_many(items: list[EnrichmentInput], *, phi: float) -> dict[str, EnrichmentResult]:
    """Calculate independent species partitioning, rejecting duplicate species IDs."""
    if len({item.species_id for item in items}) != len(items):
        raise ValueError("species IDs must be unique")
    return {item.species_id: calculate_enrichment(item, phi=phi) for item in items}
