"""Explicit display-source file binding; no inferred annotation or approval."""
from hashlib import sha256
import json
from pathlib import Path

from pydantic import Field

from .display_resources import StructureAnnotations, MAX_SOURCE_BYTES
from .models import Contract, WorkflowError


class AnnotationBindingRequest(Contract):
    project_id: str
    expected_revision: int
    source_file_id: str
    target_file_id: str
    reference_file_id: str | None = None
    sequence_file_id: str | None = None
    sequence_id: str | None = Field(default=None, min_length=1)


def bind_annotation(request, resources, data_dir):
    project = resources.store.project(request.project_id)
    if project.revision != request.expected_revision:
        raise WorkflowError("project_revision_conflict", status_code=409)
    source, _, name = resources.source(project.id, request.source_file_id)
    if source.suffix.lower() != ".json":
        raise WorkflowError("annotation_requires_json")
    raw = resources.boundary.check_original(source)
    if not isinstance(raw, dict):
        raise WorkflowError("annotation_requires_json")
    _, target, _ = resources.source(project.id, request.target_file_id)
    def set_binding(value, key, selected):
        if key in value and value[key] not in (None, selected):
            raise WorkflowError("annotation_binding_conflict")
        value[key] = selected
    raw.setdefault("schema_version", "structure-display-annotations-v1")
    set_binding(raw, "target_sha256", target.source_sha256)
    if request.reference_file_id:
        _, reference, _ = resources.source(project.id, request.reference_file_id)
        rows, overlays = raw.get("rows", []), raw.get("overlays", [])
        if not isinstance(rows, list) or not isinstance(overlays, list) or not all(isinstance(entry, dict) for entry in [*rows, *overlays]):
            raise WorkflowError("annotation_requires_json")
        for entry in [*rows, *overlays]:
            if ("reference_residue" in entry and entry["reference_residue"] is not None) or "matrix" in entry:
                set_binding(entry, "reference_sha256", reference.source_sha256)
    if request.sequence_file_id:
        _, sequence, _ = resources.source(project.id, request.sequence_file_id)
        set_binding(raw, "fusion_sequence_file_sha256", sequence.source_sha256)
        set_binding(raw, "fusion_sequence_id", request.sequence_id)
    elif request.sequence_id:
        raise WorkflowError("structure_sequence_mapping_not_authorized")
    annotation = StructureAnnotations.model_validate(raw)
    resources.validate_annotation(project.id, request.target_file_id, annotation)
    # A previously selected source is not silently replaced or made ambiguous.
    current, _ = resources.structure(project.id, request.target_file_id)
    if current["annotation_file_id"]:
        existing, _, existing_name = resources.source(project.id, current["annotation_file_id"])
        previous = StructureAnnotations.model_validate_json(existing.read_bytes())
        if previous != annotation:
            raise WorkflowError("structure_annotations_already_linked", status_code=409)
        file = resources.boundary.asset(existing, project_id=project.id, logical_name=existing_name)
    else:
        encoded = json.dumps(annotation.model_dump(mode="json"), ensure_ascii=False, indent=2).encode()
        if len(encoded) > MAX_SOURCE_BYTES:
            raise WorkflowError("display_source_budget_exceeded")
        root = data_dir / "imports"
        root.mkdir(parents=True, exist_ok=True)
        destination = root / (sha256(encoded).hexdigest() + ".json")
        destination.write_bytes(encoded)
        file = resources.boundary.asset(destination, logical_name=Path(name).stem + ".linked.json")
    return {"kind": "structure_annotations", "patch": {}, "file": file}
