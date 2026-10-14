"""DAG/ledger protocol tests; no authentic predictor is imitated."""
import pytest

from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Project, SequenceRecord
from igem_drylab.workflow.store import WorkflowStore


@pytest.mark.integration
def test_original_method_fanout_cheap_veto_and_persistent_missing_evidence(tmp_path):
    project = Project(id="p", name="Explicit software fixture", sequences=[
        SequenceRecord(id="bad", sequence="LLLLLLLLLLLL", role="enzyme_ligand_linker"),
        SequenceRecord(id="short", sequence="GSGSGSGSGSGS", role="enzyme_ligand_linker"),
        SequenceRecord(id="long", sequence="GSTSSGGGGGSGGSGGSGGS", role="scaffold_linker"),
        SequenceRecord(id="untyped", sequence="GSAD")])
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts", max_workers=2)
    workflow = recommend(project, "m1_sequence_checks")
    decisions = next(node for node in workflow.nodes if node.id == "m1_decisions")
    assert decisions.dependencies() == {"m1_fields", "m1_iupred2a", "m1_seg", "m1_jpred", "m1_signalp", "m1_deeptmhmm", "m1_tango", "m1_pscore", "m1_catgranule",'m1_fuzdrop'}
    assert workflow.nodes[-1].dependencies() == {"m1_decisions"}
    run_id = engine.create(project, workflow)
    result = engine.run(run_id)
    assert result["status"] == "succeeded", result["nodes"]
    rows = next(row for row in result["nodes"] if row["id"] == "m1_decisions")["output"]["items"]
    assert [row["verdict"] for row in rows] == ["reject", "blocked", "blocked", "blocked"]
    predictor = next(row for row in result["nodes"] if row["id"] == "m1_iupred2a")["output"]["items"]
    assert predictor[0]["tool_status"] == "not_eligible"
    assert predictor[1]["tool_status"] == "not_configured"
    assert rows[2]["precheck"]["features"]["length"] == 20
    assert len(rows[1]["steps"]) == 5
    reopened = WorkflowStore(tmp_path / "ledger.sqlite").run(run_id)
    assert next(row for row in reopened["nodes"] if row["id"] == "m1_decisions")["output"]["items"] == rows


@pytest.mark.data_contract
def test_m1_screen_rejects_unregistered_file_bearing_observations(tmp_path):
    from igem_drylab.workflow.m1_checks import M1DecisionInput, decision, precheck, m1_workflow
    from igem_drylab.workflow.tools import NodeContext
    definition = m1_workflow().nodes[0].inputs
    payload = M1DecisionInput(item=SequenceRecord(id="x", sequence="GSGSGSGS", role="enzyme_ligand_linker"),
        feature_definitions=definition["feature_definitions"].value, rules=definition["rules"].value)
    context = NodeContext(run_id="r", node_id="n", work_dir=tmp_path)
    payload.prechecks = [precheck(payload, context)]
    with pytest.raises(ValueError, match="registered_upstream"):
        decision(payload, context)
