"""Typed, review-only evidence contracts; none are production parameters."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from igem_drylab.parameters import ParameterRecord


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


def evidence_to_parameter_candidate(evidence: QuantitativeEvidence, *, requirement_name: str, parameter_type: str, canonical_unit: str, enzyme_id: str | None = None, substrate_id: str | None = None, product_id: str | None = None) -> ParameterRecord:
    """Create an extracted review candidate; callers must never auto-approve it."""
    return ParameterRecord(parameter_id=f"evidence:{evidence.doi}:{requirement_name}", name=requirement_name, value=evidence.value, unit=evidence.unit, parameter_type=parameter_type, enzyme_id=enzyme_id, substrate_id=substrate_id, product_id=product_id, source_type="literature", derivation_type="literature_extraction", source_reference=evidence.doi, doi=evidence.doi, evidence_text=evidence.evidence_text, evidence_location=evidence.evidence_location, conditions={key: value for key, value in {"host": evidence.host, "strain": evidence.strain, "assay_system": evidence.assay_system, "temperature_c": evidence.temperature_c, "pH": evidence.pH}.items() if value is not None}, uncertainty=None if evidence.uncertainty is None else {"value": evidence.uncertainty, "type": evidence.uncertainty_type}, review_status="extracted", construct_id=evidence.construct_id, condition_id=evidence.condition_id, notes="Requires human review and approval before Registry use.")
