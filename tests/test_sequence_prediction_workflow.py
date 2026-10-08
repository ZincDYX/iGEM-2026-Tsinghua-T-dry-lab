"""Actual subprocess/ledger protocol, not an authentic predictor smoke test."""
from pathlib import Path
import sys

from igem_drylab.workflow.builtins import builtin_tools
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Project, SequenceRecord, Workflow, WorkflowNode, ProjectInput
from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
from igem_drylab.workflow.store import WorkflowStore


def test_unconfigured_tool_is_recorded_without_mock_prediction(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    project = Project(id="p", name="PROTOCOL_FIXTURE", sequences=[SequenceRecord(id="input", sequence="GSAD")])
    workflow = Workflow(id="w", name="diagnostic", nodes=[WorkflowNode(id="seg", label="SEG", tool_id="prediction.seg",
        inputs={"item": ProjectInput(path=["sequences", 0])})])
    run = engine.run(engine.create(project, workflow))
    output = run["nodes"][0]["output"]
    assert output["tool_status"] == "not_configured" and output["parsed"] is None
    assert output["scientific_status"] == "diagnostic_not_formal_M1_M2_acceptance"


def test_real_subprocess_output_and_record_persist_across_ledger_reopen(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    script = tmp_path / "protocol_fixture.py"
    script.write_text("print('>input\\nGSXX\\n')\n")
    RuntimeProfiles(store).install("owned", {"seg": {"enabled": True, "mode": "external",
        "command": f'"{sys.executable}" "{script}"', "verified_version": "PROTOCOL_FIXTURE_NOT_SEG"}})
    project = Project(id="p", name="PROTOCOL_FIXTURE", runtime_profile_ref="owned",
        sequences=[SequenceRecord(id="input", sequence="GSAD")])
    workflow = Workflow(id="w", name="diagnostic", nodes=[WorkflowNode(id="seg", label="SEG", tool_id="prediction.seg",
        inputs={"item": ProjectInput(path=["sequences", 0])})])
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    run_id = engine.create(project, workflow)
    run = engine.run(run_id)
    assert run["status"] == "succeeded", run["nodes"]
    output = run["nodes"][0]["output"]
    assert output["tool_status"] == output["parse_status"] == "succeeded"
    assert output["parsed"]["low_complexity_positions"] == [3, 4]
    reopened = WorkflowStore(tmp_path / "ledger.sqlite").run(run_id)
    assert reopened["nodes"][0]["output"] == output
    assert Path(output["parsed"]["source_file"]).is_file()
