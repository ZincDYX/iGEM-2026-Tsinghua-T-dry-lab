"""Typed, review-only evidence contracts; none are production parameters."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class EvidenceMetadata(BaseModel):
    doi: str
    evidence_text: str
    evidence_location: str | None = None
    host: str | None = None
    strain: str | None = None
    assay_system: str | None = None
    temperature_c: float | None = None
    pH: float | None = None
    construct_id: str | None = None
    condition_id: str | None = None
    measurement_status: Literal["measured", "derived"] = "measured"


class QuantitativeEvidence(EvidenceMetadata):
    value: float
    unit: str
    uncertainty: float | None = Field(default=None, ge=0)
    uncertainty_type: Literal["sd", "sem", "ci"] | None = None
    replicate_count: int | None = Field(default=None, ge=1)


class EnzymeKineticsEvidence(QuantitativeEvidence):
    enzyme_id: str
    substrate_id: str
    product_id: str | None = None
    parameter: Literal["kcat", "km"]


class LlpsPartitioningEvidence(QuantitativeEvidence):
    species_id: str
    parameter: Literal["phi", "partition_coefficient"]


class ProteinAbundanceEvidence(QuantitativeEvidence):
    enzyme_id: str


class RecruitmentBindingEvidence(QuantitativeEvidence):
    enzyme_id: str | None = None
    parameter: Literal["kd", "site_abundance", "hill_coefficient"]
