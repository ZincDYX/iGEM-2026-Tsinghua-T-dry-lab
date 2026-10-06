"""Versioned ledger-backed map view; never synthesize a successful child."""
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Literal
from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence, SequenceFeatures, ProtParamEvidence
from pydantic import ValidationError
from .models import Contract
from .store import canonical


class SequenceMetricsView(Contract):
    schema_version: Literal["sequence-metrics-v1"]
    id: str
    role: str
    features: SequenceFeatures
    protparam: ProtParamEvidence
    interpretation: str


class SequenceMetricRow(Contract):
    node_id: str
    sequence_id: str | None
    sequence_sha256: str | None
    attempt: int
    status: str
    artifact_id: str | None
    artifact_sha256: str | None
    metrics: SequenceMetricsView | None
    issue: str | None


class SequenceMapView(Contract):
    schema_version: Literal["sequence-metrics-map-view-v1"] = "sequence-metrics-map-view-v1"
    run_id: str
    project_id: str
    snapshot_hash: str
    parent_node_id: str
    parent_attempt: int
    parent_artifact_id: str | None
    parent_artifact_sha256: str | None
    tool_identity: dict[str, Any]
    total_count: int
    offset: int
    rows: list[SequenceMetricRow]


def file_digest(path):
    digest = sha256()
    with Path(path).open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def sequence_map(db, run_id, node_id, offset, limit):
    run = db.execute("SELECT project_id,snapshot_hash,json_extract(snapshot,'$.workflow.nodes') AS definitions,json_extract(snapshot,'$.tools') AS tools FROM runs WHERE id=?", (run_id,)).fetchone()
    definition = next((item for item in json.loads(run["definitions"]) if item["id"] == node_id), None)
    if not definition or definition["tool_id"] != "fusion.sequence_metrics" or not definition.get("map"):
        return None
    count = db.execute("SELECT COUNT(*) FROM nodes WHERE run_id=? AND parent_id=?", (run_id, node_id)).fetchone()[0]
    parent = db.execute("SELECT n.status,n.attempts,json_array_length(n.output,'$.items') AS item_count,a.id AS artifact_id,a.hash AS artifact_hash,a.path AS artifact_path FROM nodes n LEFT JOIN artifacts a ON a.run_id=n.run_id AND a.node_id=n.id AND json_extract(a.metadata,'$.attempt')=n.attempts WHERE n.run_id=? AND n.id=?", (run_id, node_id)).fetchone()
    parent_issue = None
    if parent["status"] == "succeeded":
        if not parent["artifact_path"]:
            parent_issue = "missing_registered_parent_artifact"
        else:
            try:
                if file_digest(parent["artifact_path"]) != parent["artifact_hash"]:
                    parent_issue = "sequence_parent_artifact_hash_mismatch"
            except OSError:
                parent_issue = "unreadable_parent_artifact"
    items = [json.loads(row[0]) for row in db.execute("SELECT value FROM nodes,json_each(nodes.output,'$.items') WHERE run_id=? AND nodes.id=? LIMIT ? OFFSET ?", (run_id,node_id,limit,offset))]
    rows = []
    children = db.execute("SELECT n.id,n.status,n.attempts,n.inputs,n.output,a.id AS artifact_id,a.hash AS artifact_hash,a.path AS artifact_path FROM nodes n LEFT JOIN artifacts a ON a.run_id=n.run_id AND a.node_id=n.id AND json_extract(a.metadata,'$.attempt')=n.attempts WHERE n.run_id=? AND n.parent_id=? ORDER BY n.rowid LIMIT ? OFFSET ?", (run_id, node_id, limit, offset))
    for index, child in enumerate(children, offset):
        inputs = json.loads(child["inputs"]) if child["inputs"] else {}
        sequence = inputs.get(definition["map"]["item_argument"], {})
        if not isinstance(sequence, dict):
            sequence = {}
        output = json.loads(child["output"]) if child["output"] else None
        digest = None
        issue = None
        try:
            digest = sha256(normalize_amino_acid_sequence(sequence["sequence"]).encode()).hexdigest()
        except (ValueError, KeyError, TypeError):
            issue = "invalid_sequence_input_identity"
        metrics = None
        if child["status"] == "succeeded":
            try:
                if not isinstance(output, dict):
                    raise ValueError("unknown_sequence_result_schema")
                # Explicit legacy read adapter adds only the display schema tag,
                # never a scientific value; raw artifacts remain unchanged.
                value = SequenceMetricsView.model_validate({"schema_version": "sequence-metrics-v1", **output})
                if value.id != sequence.get("id") or value.features.sequence_sha256 != digest or value.protparam.input_sha256 != digest:
                    issue = "sequence_result_identity_mismatch"
                elif not child["artifact_path"]:
                    issue = "missing_registered_artifact"
                elif file_digest(child["artifact_path"]) != child["artifact_hash"] or sha256(canonical(output).encode()).hexdigest() != child["artifact_hash"]:
                    issue = "sequence_artifact_hash_mismatch"
                elif parent["status"] == "succeeded" and (parent["item_count"] != count or index-offset >= len(items) or items[index-offset] != output):
                    issue = "sequence_aggregate_child_mismatch"
                elif parent_issue:
                    issue = parent_issue
                elif issue is None:
                    metrics = value
            except (ValidationError, ValueError, OSError):
                issue = "unknown_or_unreadable_sequence_result"
        else:
            issue = child["status"]
        rows.append(SequenceMetricRow(node_id=child["id"], sequence_id=sequence.get("id"), sequence_sha256=digest,
            attempt=child["attempts"], status=child["status"], artifact_id=child["artifact_id"], artifact_sha256=child["artifact_hash"],
            metrics=metrics, issue=issue))
    identity = json.loads(run["tools"]).get("fusion.sequence_metrics", {})
    identity = {key: identity[key] for key in ("version", "runtime", "plugin_hash", "implementation_sha256") if key in identity}
    return SequenceMapView(run_id=run_id, project_id=run["project_id"], snapshot_hash=run["snapshot_hash"], parent_node_id=node_id,
        parent_attempt=parent["attempts"], parent_artifact_id=parent["artifact_id"], parent_artifact_sha256=parent["artifact_hash"],
        tool_identity=identity, total_count=count, offset=offset, rows=rows).model_dump(mode="json")
