"""Read-only, hash-bound FASTA display index; not a second model input."""
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from typing import Literal
from Bio import SeqIO
from .models import Contract, SequenceRef, SequenceRecord, WorkflowError
from pydantic import Field


class SequenceIndexView(Contract):
    status: Literal["indexed", "not_indexed"]
    file_id: str
    source_sha256: str
    count: int | None
    reason_code: str | None


def sequence_index(science, asset, db):
    source = science.config.inputs.protein_fasta.resolve()
    expected = next((item.sha256 for item in science.evidence_files if item.path.resolve() == source), None)
    state = source.stat()
    signature = [str(source), state.st_size, state.st_mtime_ns, state.st_ctime_ns]
    row = db.execute("SELECT payload FROM sequence_indexes WHERE hash=?", (expected,)).fetchone()
    metadata = json.loads(row[0]) if row else None
    if metadata is None or signature not in metadata.get("validated_sources", []):
        raw = source.read_bytes()
        if expected != sha256(raw).hexdigest():
            raise WorkflowError("file_identity_changed", status_code=409)
        if metadata is not None:
            metadata.setdefault("validated_sources", []).append(signature)
            db.execute("UPDATE sequence_indexes SET payload=? WHERE hash=?", (json.dumps(metadata), expected))
    if metadata is None:
        try:
            text = raw.decode("utf-8-sig")
            if text.strip() and not text.lstrip().startswith(">"):
                raise ValueError("invalid_fasta_header")
            records = list(SeqIO.parse(StringIO(text), "fasta"))
            if any(not record.id or not record.seq for record in records):
                raise ValueError("empty_fasta_record")
            if len({record.id for record in records}) != len(records):
                raise ValueError("duplicate_fasta_identifier")
            entries = [{"id": record.id, "sequence_sha256": sha256(str(record.seq).upper().encode()).hexdigest(), "length": len(record.seq)} for record in records]
            metadata = {"status": "indexed", "count": len(entries), "reason_code": None, "entries": entries}
        except (ValueError, UnicodeError):
            metadata = {"status": "not_indexed", "count": None, "reason_code": "fasta_parse_failed", "entries": []}
        metadata["validated_sources"] = [signature]
        db.execute("INSERT OR IGNORE INTO sequence_indexes VALUES(?,?)", (expected, json.dumps(metadata)))
    return SequenceIndexView(**{key: metadata[key] for key in ("status", "count", "reason_code")},
                             file_id=asset["id"], source_sha256=expected).model_dump(mode="json")


class SequenceChoice(Contract):
    ref: SequenceRef
    label: str
    length: int = Field(ge=1)
    role: str
    localization_context: Literal["cytosolic", "er_anchored"] = "cytosolic"


class SequencePage(Contract):
    project_id: str
    project_revision: int
    offset: int
    total: int
    items: list[SequenceChoice]


def _role(config: dict, identifier: str) -> str:
    inputs = config["inputs"]
    declared = inputs.get("sequence_roles", {}).get(identifier)
    if declared:
        return declared
    if any(item["id"] == identifier for item in inputs.get("constructs", [])):
        return "full_fusion"
    if inputs.get("idr_id") == identifier:
        return "idr"
    if any(item["protein_id"] == identifier for item in inputs.get("enzymes", [])):
        return "enzyme"
    return "unspecified"


def _localization_context(config: dict, identifier: str) -> str:
    # Use the declared full construct, never a FASTA identifier heuristic.
    matches = [item for item in config["inputs"].get("constructs", []) if item["id"] == identifier]
    return (matches[0].get("localization_context") or "cytosolic") if matches else "cytosolic"


def sequence_page(project, boundary, offset: int, limit: int) -> SequencePage:
    choices = []
    for item in project.sequences:
        choices.append(SequenceChoice(ref=SequenceRef(source="project", record_id=item.id,
            sequence_sha256=sha256(item.sequence.encode()).hexdigest(), construct_version=project.revision),
            label=item.id, length=len(item.sequence), role=item.role,
            localization_context=item.localization_context))
    if project.scientific_project:
        from .scientific_project import ScientificProject
        science = ScientificProject.model_validate(project.scientific_project)
        with boundary.store.connection() as db:
            asset = boundary.asset(science.config.inputs.protein_fasta, project_id=project.id, db=db)
            view = sequence_index(science, asset, db)
            row = db.execute("SELECT payload FROM sequence_indexes WHERE hash=?", (view["source_sha256"],)).fetchone()
        if view["status"] == "indexed":
            config = science.config.model_dump(mode="json")
            for item in json.loads(row[0])["entries"]:
                choices.append(SequenceChoice(ref=SequenceRef(source="scientific_fasta", file_id=asset["id"],
                    record_id=item["id"], sequence_sha256=item["sequence_sha256"], construct_version=project.revision),
                    label=item["id"], length=item["length"], role=_role(config, item["id"]),
                    localization_context=_localization_context(config, item["id"])))
    return SequencePage(project_id=project.id, project_revision=project.revision, offset=offset,
        total=len(choices), items=choices[offset:offset + limit])


def resolve_sequence_ref(ref: SequenceRef, project: dict, store) -> dict:
    """Resolve at execution from the frozen source, never a UI array position.

    Browser cache signatures are not sufficient here: FASTA bytes are verified
    against the scientific snapshot before the selected record is used.
    """
    if ref.construct_version != project["revision"]:
        raise WorkflowError("sequence_reference_revision_mismatch", status_code=409)
    if ref.source == "project":
        if ref.file_id is not None:
            raise WorkflowError("sequence_reference_source_mismatch")
        matches = [item for item in project["sequences"] if item["id"] == ref.record_id]
    else:
        science = project.get("scientific_project")
        if not science or ref.file_id is None:
            raise WorkflowError("sequence_reference_source_missing")
        source = Path(science["config"]["inputs"]["protein_fasta"]).resolve()
        with store.connection() as db:
            asset = db.execute("SELECT path,project_id FROM file_assets WHERE id=?", (ref.file_id,)).fetchone()
        if not asset or asset["project_id"] != project["id"] or Path(asset["path"]).resolve() != source:
            raise WorkflowError("file_project_mismatch", status_code=403)
        expected = next((item["sha256"] for item in science["evidence_files"] if Path(item["path"]).resolve() == source), None)
        raw = source.read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise WorkflowError("file_identity_changed", status_code=409)
        matches = [dict(id=item.id, sequence=str(item.seq).upper(), role=_role(science["config"], item.id),
                        localization_context=_localization_context(science["config"], item.id))
                   for item in SeqIO.parse(StringIO(raw.decode("utf-8-sig")), "fasta") if item.id == ref.record_id]
    if len(matches) != 1 or sha256(matches[0]["sequence"].encode()).hexdigest() != ref.sequence_sha256:
        raise WorkflowError("sequence_reference_identity_mismatch", status_code=409)
    return SequenceRecord.model_validate(matches[0]).model_dump(mode="json")


def stored_scientific_count(project, db):
    science = project.get("scientific_project")
    if not science:
        return None, "not_attached"
    source = Path(science["config"]["inputs"]["protein_fasta"]).resolve()
    expected = next((item["sha256"] for item in science["evidence_files"] if Path(item["path"]).resolve() == source), None)
    row = db.execute("SELECT json_extract(payload,'$.count') AS count,json_extract(payload,'$.status') AS status FROM sequence_indexes WHERE hash=?", (expected,)).fetchone()
    if not row:
        return None, "not_indexed"
    return row["count"], row["status"]
