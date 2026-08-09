"""Typed, review-only evidence contracts; none are production parameters."""
from __future__ import annotations
from typing import Literal
import hashlib
from pydantic import BaseModel, ConfigDict, Field
from igem_drylab.parameters import ParameterRecord
from igem_drylab.parameters.requirements import ParameterRequirement
from igem_drylab.parameters.dimensions import normalize_for_requirement


class EvidenceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    parameter: Literal["partition_coefficient"]


class PhaseVolumeEvidence(QuantitativeEvidence):
    parameter: Literal["phi"] = "phi"


class ProteinAbundanceEvidence(QuantitativeEvidence):
    enzyme_id: str


class RecruitmentBindingEvidence(QuantitativeEvidence):
    enzyme_id: str | None = None
    parameter: Literal["kd", "site_abundance", "hill_coefficient"]


class PhaseActivityEvidence(QuantitativeEvidence):
    enzyme_id: str
    phase: Literal["dense", "dilute"]
    parameter: Literal["residual_activity"] = "residual_activity"


class DegradationRateEvidence(QuantitativeEvidence):
    species_id: str
    parameter: Literal["degradation_rate"] = "degradation_rate"


def map_evidence_to_requirement(evidence: QuantitativeEvidence, requirement: ParameterRequirement) -> ParameterRecord:
    """Validate typed evidence against one declared requirement and create an extracted candidate."""
    enzyme = getattr(evidence, "enzyme_id", None)
    substrate = getattr(evidence, "substrate_id", None)
    product = getattr(evidence, "product_id", None)
    species = getattr(evidence, "species_id", None)
    phase = getattr(evidence, "phase", None)
    expected = {
        EnzymeKineticsEvidence: {"kcat": "kcat", "km": "km"},
        LlpsPartitioningEvidence: {"partition_coefficient": "kp"},
        PhaseVolumeEvidence: {"phi": "phi"},
        ProteinAbundanceEvidence: {None: "abundance"},
        RecruitmentBindingEvidence: {"kd": "kd", "site_abundance": "abundance", "hill_coefficient": "hill_coefficient"},
        PhaseActivityEvidence: {"residual_activity": "activity_ratio"},
        DegradationRateEvidence: {"degradation_rate": "degradation_rate"},
    }
    semantic = expected.get(type(evidence), {}).get(getattr(evidence, "parameter", None))
    if semantic != requirement.parameter_type:
        raise ValueError("evidence measurement semantics do not match requirement")
    if requirement.enzyme_id and enzyme != requirement.enzyme_id:
        raise ValueError("evidence enzyme identity does not match requirement")
    if requirement.substrate_id and substrate != requirement.substrate_id:
        raise ValueError("evidence substrate identity does not match requirement")
    if requirement.product_id and product != requirement.product_id:
        raise ValueError("evidence product identity does not match requirement")
    if requirement.species_id and species != requirement.species_id:
        raise ValueError("evidence species identity does not match requirement")
    if requirement.phase and phase != requirement.phase:
        raise ValueError("evidence phase does not match requirement")
    normalize_for_requirement(evidence.value, evidence.unit, requirement)
    return evidence_to_parameter_candidate(evidence, requirement_name=requirement.name, parameter_type=requirement.parameter_type, canonical_unit=requirement.canonical_unit, enzyme_id=requirement.enzyme_id, substrate_id=requirement.substrate_id, product_id=requirement.product_id, species_id=requirement.species_id)


def evidence_to_parameter_candidate(evidence: QuantitativeEvidence, *, requirement_name: str, parameter_type: str, canonical_unit: str, enzyme_id: str | None = None, substrate_id: str | None = None, product_id: str | None = None, species_id: str | None = None) -> ParameterRecord:
    """Create an extracted review candidate; callers must never auto-approve it."""
    identity = "|".join(str(value or "") for value in (evidence.doi, requirement_name, evidence.evidence_location, evidence.construct_id, evidence.condition_id, evidence.evidence_text))
    stable_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    derivation = "other" if evidence.measurement_status == "measured" else "literature_extraction"
    return ParameterRecord(parameter_id=f"evidence:{stable_id}", name=requirement_name, value=evidence.value, unit=evidence.unit, parameter_type=parameter_type, species_id=species_id, enzyme_id=enzyme_id, substrate_id=substrate_id, product_id=product_id, source_type="literature", derivation_type=derivation, source_reference=evidence.doi, doi=evidence.doi, evidence_text=evidence.evidence_text, evidence_location=evidence.evidence_location, conditions={key: value for key, value in {"host": evidence.host, "strain": evidence.strain, "assay_system": evidence.assay_system, "temperature_c": evidence.temperature_c, "pH": evidence.pH, "phase": getattr(evidence, "phase", None), "measurement_status": evidence.measurement_status, "evidence_type": type(evidence).__name__, "replicate_count": evidence.replicate_count}.items() if value is not None}, uncertainty=None if evidence.uncertainty is None else {"value": evidence.uncertainty, "type": evidence.uncertainty_type}, review_status="extracted", construct_id=evidence.construct_id, condition_id=evidence.condition_id, notes="Requires human review and approval before Registry use.")
