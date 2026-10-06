"""Scientific computation regression; run on the server, never locally.

Compare the original 12-source-record statistics from independent review
evidence with the production handler. This establishes statistical replay only,
not cloning, localization, LLPS, assembly or experiment validation.
"""
from hashlib import sha256
import json
from pathlib import Path

from Bio import SeqIO

from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Project, SequenceRecord
from igem_drylab.workflow.sequence_results import sequence_map
from igem_drylab.workflow.store import WorkflowStore


def test_original_twelve_statistics_replay_with_production_tool_and_registered_parent(tmp_path):
    fixture = Path(__file__).parent / "fixtures/r7_sequence_display"
    fasta = fixture / "source.fasta"
    raw = fasta.read_bytes()
    assert sha256(raw).hexdigest() == "fc1f91bdec45e4be79df7885e9ea3bb3caf7bb14a5094ba5cad323585c5f7cb2"
    evidence = (fixture / "parent_result.json").read_bytes()
    assert sha256(evidence).hexdigest() == "327517dff153fef04fc94a498985869c22f80e5f9115c85dbbe17ea8799cfc77"
    expected = json.loads(evidence)["node"]["output"]["items"]
    project = Project(id="source-statistics-replay", name="Original-source statistical replay",
        sequences=[SequenceRecord(id=record.id, sequence=str(record.seq)) for record in SeqIO.parse(fasta, "fasta")],
        files=[{"path": str(fasta), "sha256": sha256(raw).hexdigest(), "name": "source.fasta"}])
    store = WorkflowStore(tmp_path / "ledger.sqlite3")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    run_id = engine.create(project, recommend(project, "fusion_screen"))
    actual = engine.run(run_id)
    assert actual["status"] == "succeeded"
    parent = next(node for node in actual["nodes"] if node["id"] == "sequences")
    assert parent["output"]["items"] == [{"schema_version": "sequence-metrics-v1", **item} for item in expected]
    with store.connection() as db:
        view = sequence_map(db, run_id, "sequences", 0, 20)
    assert view["total_count"] == 12 and len(view["rows"]) == 12
    assert view["tool_identity"]["version"] == "2"
    assert all(row["issue"] is None and row["metrics"] is not None for row in view["rows"])
    assert [row["sequence_sha256"] for row in view["rows"]] == [item["features"]["sequence_sha256"] for item in expected]
    assert fasta.read_bytes() == raw and (fixture / "parent_result.json").read_bytes() == evidence
