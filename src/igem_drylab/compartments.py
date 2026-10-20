"""Scenario routing shared by stage boundaries, not a membrane solver.

The historical cytosolic method remains unchanged. An ER construct or design
cannot be made cytosolic by an old/default downstream assessment.
"""
from typing import Literal
from pathlib import Path
from hashlib import sha256
import re
from pydantic import BaseModel, ConfigDict, Field, model_validator

CompartmentScenario = Literal["cytosolic_two_phase", "er_anchored"]


class CompartmentContract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ArtifactReference(CompartmentContract):
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    def verify(self):
        with self.path.open("rb") as stream:
            digest = sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != self.sha256:
            raise ValueError("ER_source_artifact_identity_changed")


class ResidueRange(CompartmentContract):
    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("residue_range_is_one_based_inclusive_and_ordered")
        return self


class ScientificQuantity(CompartmentContract):
    """Canonical value with a registry binding; numerical controls are separate."""
    value: float = Field(ge=0)
    unit: Literal["uM", "umol", "L", "um2", "copies/um2", "1", "L/h", "1/h", "umol/h"]
    entity_basis: str = Field(min_length=1)
    parameter_id: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)

    def require(self, unit: str, *, positive=False):
        if self.unit != unit or (positive and self.value <= 0):
            raise ValueError("ER_quantity_unit_or_positive_value_mismatch:" + unit)
        return self.value


class MembraneTopologyEvidence(CompartmentContract):
    evidence_id: str
    construct_id: str
    construct_version: str
    condition_id: str
    input_sequence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor: ResidueRange
    anchor_source_record: str = Field(min_length=1)
    tool: Literal["DeepTMHMM"]
    tool_version: str = Field(min_length=1)
    native_record_id: str
    native_output: ArtifactReference
    body_side: Literal["cytosolic", "luminal", "unknown"]
    orientation_source: str | None
    cleavage_state: Literal["not_cleaved", "cleaved", "unknown"]
    body_removed_by_cleavage: bool | None
    cleavage_source: str | None
    evidence_level: Literal["predicted", "experimentally_supported"]
    raw_references: list[ArtifactReference] = Field(min_length=1)
    review_parameter_ids: dict[Literal["body_side", "cleavage_state", "body_retained"],str] = Field(default_factory=dict)


def evaluate_topology(evidence: MembraneTopologyEvidence, sequence: str) -> dict:
    """Read the exact native topology, retaining unknown ER-side evidence.

    Native I/O labels alone are not experimental proof of cytosolic/luminal
    orientation in this fusion. No sequence padding, prediction or cleavage
    state is invented here.
    """
    from .fusion_tool_import import NativeFusionArtifact, parse_native_artifact
    if sha256(sequence.encode()).hexdigest() != evidence.input_sequence_sha256:
        raise ValueError("ER_topology_sequence_identity_mismatch")
    if evidence.anchor.end > len(sequence):
        raise ValueError("ER_anchor_range_exceeds_construct")
    for artifact in [evidence.native_output, *evidence.raw_references]:
        artifact.verify()
    parse_native_artifact(NativeFusionArtifact(path=evidence.native_output.path,
        tool_version=evidence.tool_version, format="deeptmhmm1_3line", record_id=evidence.native_record_id), sequence)
    lines = [line.strip() for line in evidence.native_output.path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    labels = next(lines[i+2] for i in range(0,len(lines),3)
        if lines[i][1:].split("|")[0].strip().split()[0] == evidence.native_record_id)
    segments = [{"start":m.start()+1, "end":m.end(),
        "before_label":labels[m.start()-1] if m.start() else None,
        "after_label":labels[m.end()] if m.end() < len(labels) else None} for m in re.finditer("M+", labels)]
    expected = [item for item in segments if evidence.anchor.start <= item["start"] and item["end"] <= evidence.anchor.end]
    unexpected = [item for item in segments if item not in expected]
    flags = []
    if not expected: flags.append("expected_anchor_TM_not_observed")
    if unexpected: flags.append("unexpected_TM_outside_declared_anchor")
    if evidence.body_side == "unknown" or not evidence.orientation_source:
        flags.append("scaffold_body_side_not_established")
    if evidence.body_side == "luminal": flags.append("luminal_body_requires_a_separately_supported_model")
    if evidence.cleavage_state == "unknown" or not evidence.cleavage_source or evidence.body_removed_by_cleavage is None:
        flags.append("anchor_cleavage_and_body_retention_not_established")
    if evidence.body_removed_by_cleavage: flags.append("scaffold_body_removed_by_cleavage")
    return {"schema_version":"membrane-topology-v1", "evidence_id":evidence.evidence_id,
        "construct_id":evidence.construct_id, "condition_id":evidence.condition_id,
        "anchor":evidence.anchor.model_dump(), "anchor_source_record":evidence.anchor_source_record,
        "predicted_segments":segments, "unexpected_segments":unexpected,
        "body_side":evidence.body_side, "cleavage_state":evidence.cleavage_state,
        "evidence_level":evidence.evidence_level, "flags":flags,
        "status":"review" if flags else "prediction_consistent_with_design",
        "quantitative_ER_ready":False,
        "review_binding_required":True,
        "claim_scope":"topology_evidence_not_enzyme_activity_or_LLPS_validation"}


def resolve_contract_paths(value, base_dir: Path):
    """Resolve typed artifact paths, including dictionary-valued stage requests."""
    if isinstance(value, BaseModel):
        for key in type(value).model_fields:
            child = getattr(value,key)
            if isinstance(child,Path):
                setattr(value,key,(base_dir/child).resolve() if not child.is_absolute() else child.resolve())
            else:
                resolve_contract_paths(child,base_dir)
    elif isinstance(value,dict):
        for child in value.values(): resolve_contract_paths(child,base_dir)
    elif isinstance(value,(list,tuple)):
        for child in value: resolve_contract_paths(child,base_dir)


def scenario_for_construct(config, construct_id: str, definition: dict | None = None) -> CompartmentScenario:
    definitions = {item.id: item for item in config.inputs.constructs}
    for record in config.inputs.construct_records:
        if record.review_status == "approved":
            from igem_drylab.pipeline.config import ConstructDefinition
            item = ConstructDefinition.model_validate(record.candidate_definition())
            definitions[item.id] = item
    design = next((item for item in config.inputs.designs if item.id == construct_id), None)
    members = design.protein_construct_ids if design else [construct_id]
    if (definition or {}).get("localization_context") == "er_anchored":
        return "er_anchored"
    if any(definitions[item].localization_context == "er_anchored" for item in members if item in definitions):
        return "er_anchored"
    return "cytosolic_two_phase"
