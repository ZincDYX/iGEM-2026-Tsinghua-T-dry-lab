"""Read-only parsing/display identity oracles, not scientific regressions.

Independent expectations: reviewer byte hashes, 12 FASTA records, and raw child
records. Kills flatten/count-zero, hidden-failure, parent/child mixup and hash
substitution implementations. No scientific handler is executed.
"""
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

from Bio import SeqIO
import pytest

from igem_drylab.workflow.models import NodeStatus, WorkflowError
from igem_drylab.workflow.sequence_index import sequence_index, stored_scientific_count
from igem_drylab.workflow.sequence_results import sequence_map
from igem_drylab.workflow.store import WorkflowStore, canonical

FIXTURE = Path(__file__).parent / "fixtures/r7_sequence_display"


def test_original_twelve_sequence_index_is_hash_bound_and_not_a_second_input(tmp_path):
    raw = (FIXTURE / "source.fasta").read_bytes()
    digest = sha256(raw).hexdigest()
    assert digest == "fc1f91bdec45e4be79df7885e9ea3bb3caf7bb14a5094ba5cad323585c5f7cb2"
    path = tmp_path / "source.fasta"
    path.write_bytes(raw)
    science = SimpleNamespace(config=SimpleNamespace(inputs=SimpleNamespace(protein_fasta=path)),
                              evidence_files=[SimpleNamespace(path=path, sha256=digest)])
    store = WorkflowStore(tmp_path / "ledger.sqlite3")
    project = {"sequences": [], "scientific_project": {"config": {"inputs": {"protein_fasta": str(tmp_path / "unused/../source.fasta")}},
                                                     "evidence_files": [{"path": str(path), "sha256": digest}]}}
    before = deepcopy(project)
    with store.connection() as db:
        view = sequence_index(science, {"id": "authorized-file"}, db)
        assert view == {"status": "indexed", "file_id": "authorized-file", "source_sha256": digest, "count": 12, "reason_code": None}
        assert stored_scientific_count(project, db) == (12, "indexed")
        assert stored_scientific_count({"sequences": []}, db) == (None, "not_attached")
        # Independent input channels neither deduplicate nor merge each other.
        project["sequences"] = [{"id": "different", "sequence": "MAGSGS"}]
        assert stored_scientific_count(project, db) == (12, "indexed")
    project["sequences"] = []
    assert project == before
    path.write_bytes(raw + b"\n")
    with store.connection() as db, pytest.raises(WorkflowError, match="file_identity_changed"):
        sequence_index(science, {"id": "authorized-file"}, db)


@pytest.mark.parametrize("raw,count,status", [(b"", 0, "indexed"), (b"not a FASTA", None, "not_indexed"),
    (b">empty\n", None, "not_indexed"), (b">duplicate\nMA\n>duplicate\nGS\n", None, "not_indexed"),
    (b"\xff", None, "not_indexed")])
def test_empty_and_invalid_fasta_never_share_zero_meaning(tmp_path, raw, count, status):
    path = tmp_path / "source.fasta"
    path.write_bytes(raw)
    digest = sha256(raw).hexdigest()
    science = SimpleNamespace(config=SimpleNamespace(inputs=SimpleNamespace(protein_fasta=path)),
                              evidence_files=[SimpleNamespace(path=path, sha256=digest)])
    with WorkflowStore(tmp_path / "ledger.sqlite3").connection() as db:
        view = sequence_index(science, {"id": "file"}, db)
        assert view["status"] == status and view["count"] == count


def recorded_map(tmp_path):
    raw = (FIXTURE / "parent_result.json").read_bytes()
    assert sha256(raw).hexdigest() == "327517dff153fef04fc94a498985869c22f80e5f9115c85dbbe17ea8799cfc77"
    outputs = json.loads(raw)["node"]["output"]["items"]
    records = list(SeqIO.parse(StringIO((FIXTURE / "source.fasta").read_text()), "fasta"))
    assert len(records) == len(outputs) == 12
    assert [record.id for record in records] == [value["id"] for value in outputs]
    store = WorkflowStore(tmp_path / "ledger.sqlite3")
    run_id = store.create_run({"project": {"id": "source-display"}, "workflow": {"nodes": [
        {"id": "sequences", "tool_id": "fusion.sequence_metrics", "map": {"item_argument": "item"}}]},
        "tools": {"fusion.sequence_metrics": {"version": "1", "runtime": "recorded-evidence", "implementation_sha256": "a" * 64}}})
    store.expand(run_id, "sequences", [{"item": {"id": record.id, "sequence": str(record.seq)}} for record in records])
    for index, value in enumerate(outputs):
        node_id = f"sequences[{index}]"
        store.set_node(run_id, node_id, NodeStatus.running, increment=True)
        path = tmp_path / f"child-{index}.json"
        path.write_text(canonical(value), encoding="utf-8")
        store.complete_node(run_id, node_id, value, path, [])
    parent_path = tmp_path / "parent.json"
    parent_path.write_text(canonical({"items": outputs}), encoding="utf-8")
    store.complete_node(run_id, "sequences", {"items": outputs}, parent_path, [])
    return store, run_id, outputs


def test_twelve_parent_map_has_bounded_registered_child_rows_and_raw_values(tmp_path):
    store, run_id, original = recorded_map(tmp_path)
    before = store.run(run_id)
    with store.connection() as db:
        view = sequence_map(db, run_id, "sequences", 3, 2)
        assert view["schema_version"] == "sequence-metrics-map-view-v1"
        assert view["total_count"] == 12 and view["offset"] == 3
        assert view["run_id"] == run_id and view["snapshot_hash"] == before["snapshot_hash"]
        assert [row["node_id"] for row in view["rows"]] == ["sequences[3]", "sequences[4]"]
        for index, row in enumerate(view["rows"], 3):
            assert row["issue"] is None and row["attempt"] == 1
            value = row["metrics"]
            assert value.pop("schema_version") == "sequence-metrics-v1"
            assert value == original[index]  # display only, including nulls/units
            assert row["artifact_sha256"] == sha256(canonical(original[index]).encode()).hexdigest()
            assert row["sequence_sha256"] == original[index]["features"]["sequence_sha256"]
    assert store.run(run_id) == before


@pytest.mark.parametrize("kind,issue", [("failed", "failed"), ("missing_artifact", "missing_registered_artifact"),
    ("tampered", "sequence_artifact_hash_mismatch"), ("wrong_sequence", "sequence_result_identity_mismatch"),
    ("wrong_parent", "sequence_aggregate_child_mismatch"), ("unknown_schema", "unknown_or_unreadable_sequence_result"),
    ("tampered_parent", "sequence_parent_artifact_hash_mismatch")])
def test_partial_failure_and_identity_mismatch_cannot_display_success_metrics(tmp_path, kind, issue):
    store, run_id, original = recorded_map(tmp_path)
    with store.connection() as db:
        if kind == "failed":
            db.execute("UPDATE nodes SET status='failed' WHERE run_id=? AND id='sequences[0]'", (run_id,))
        elif kind == "missing_artifact":
            db.execute("DELETE FROM artifacts WHERE run_id=? AND node_id='sequences[0]'", (run_id,))
        elif kind == "tampered":
            (tmp_path / "child-0.json").write_bytes(b"tampered fixture")
        elif kind == "tampered_parent":
            (tmp_path / "parent.json").write_bytes(b"tampered fixture")
        elif kind == "wrong_sequence":
            db.execute("UPDATE nodes SET inputs=json_set(inputs,'$.item.sequence','MAGSGS') WHERE run_id=? AND id='sequences[0]'", (run_id,))
        elif kind == "wrong_parent":
            db.execute("UPDATE nodes SET output=json_set(output,'$.items[0]',json(?)) WHERE run_id=? AND id='sequences'", (canonical(original[1]), run_id))
        else:
            db.execute("UPDATE nodes SET output=json_set(output,'$.schema_version','unrecognized-v99') WHERE run_id=? AND id='sequences[0]'", (run_id,))
    with store.connection() as db:
        view = sequence_map(db, run_id, "sequences", 0, 2)
    assert view["total_count"] == 12 and len(view["rows"]) == 2
    assert view["rows"][0]["metrics"] is None and view["rows"][0]["issue"] == issue
    if kind == "tampered_parent":
        assert view["rows"][1]["metrics"] is None
    else:
        assert view["rows"][1]["metrics"]["id"] == original[1]["id"]


def test_empty_map_is_explicit_and_unknown_tool_not_inferred(tmp_path):
    store, run_id, _ = recorded_map(tmp_path)
    with store.connection() as db:
        db.execute("DELETE FROM nodes WHERE run_id=? AND parent_id='sequences'", (run_id,))
        db.execute("UPDATE nodes SET output=? WHERE run_id=? AND id='sequences'", (canonical({"items": []}), run_id))
        view = sequence_map(db, run_id, "sequences", 0, 20)
        assert view["total_count"] == 0 and view["rows"] == []
        db.execute("UPDATE runs SET snapshot=json_set(snapshot,'$.workflow.nodes[0].tool_id','unknown') WHERE id=?", (run_id,))
        assert sequence_map(db, run_id, "sequences", 0, 20) is None
