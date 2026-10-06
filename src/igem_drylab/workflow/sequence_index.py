"""Read-only, hash-bound FASTA display index; not a second model input."""
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from typing import Literal
from Bio import SeqIO
from .models import Contract


class SequenceIndexView(Contract):
    status: Literal["indexed", "not_indexed"]
    file_id: str
    source_sha256: str
    count: int | None
    reason_code: str | None


def sequence_index(science, asset, db):
    source = science.config.inputs.protein_fasta.resolve()
    expected = next((item.sha256 for item in science.evidence_files if item.path.resolve() == source), None)
    raw = source.read_bytes()
    if expected != sha256(raw).hexdigest():
        from .models import WorkflowError
        raise WorkflowError("file_identity_changed", status_code=409)
    row = db.execute("SELECT json_extract(payload,'$.status') AS status,json_extract(payload,'$.count') AS count,json_extract(payload,'$.reason_code') AS reason_code FROM sequence_indexes WHERE hash=?", (expected,)).fetchone()
    if row:
        metadata = dict(row)
    else:
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
        db.execute("INSERT OR IGNORE INTO sequence_indexes VALUES(?,?)", (expected, json.dumps(metadata)))
    return SequenceIndexView(**{key: metadata[key] for key in ("status", "count", "reason_code")},
                             file_id=asset["id"], source_sha256=expected).model_dump(mode="json")


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
