from hashlib import sha256
from pathlib import Path

import pytest

from igem_drylab.agent.models import PlanStep, ToolCallRecord
from igem_drylab.agent.recovery import ErrorRecoveryPolicy
from igem_drylab.workflow.builtins import builtin_tools
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.mcp_bridge import SCIENTIFIC_TOOLS, register_scientific_mcp
from igem_drylab.workflow.models import LiteralInput, Project, Workflow, WorkflowNode
from igem_drylab.workflow.pathway import Pathway
from igem_drylab.workflow.store import WorkflowStore
from test_workflow_platform import pathway_payload


def test_recovery_routes_structured_codes_not_message_substrings():
    step = PlanStep(step_id="n", objective="test")
    policy = ErrorRecoveryPolicy()
    record = ToolCallRecord(step_id="n", tool_name="x", arguments={}, status="failed", result={"structuredContent": {"error": {"type": "tool_error", "message": "not a timeout; malformed is merely a label"}}})
    assert policy.next_action(step, record).action == "fail"
    record.result["structuredContent"]["error"] = {"type": "timeout", "message": "localized text"}
    assert policy.next_action(step, record).action == "retry"


def test_real_workflow_calls_scientific_mcp_server(tmp_path: Path):
    tools = builtin_tools()
    register_scientific_mcp(tools)
    assert {tool["id"] for tool in tools.list() if tool["runtime"] == "mcp_stdio"} == SCIENTIFIC_TOOLS
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts")
    workflow = Workflow(id="mcp", name="real stdio", nodes=[WorkflowNode(id="protparam", label="ProtParam", tool_id="igem.m1.compute_protparam", inputs={"sequence": LiteralInput(value="MAGSGS")})])
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))
    assert result["status"] == "succeeded", result["nodes"]
    assert result["nodes"][0]["output"]["result"]["molecular_weight_da"] > 0
    assert result["snapshot"]["tools"]["igem.m1.compute_protparam"]["runtime"] == "mcp_stdio"


def test_workflow_mcp_uses_public_m2_name_and_nested_schema(tmp_path):
    tools = builtin_tools()
    register_scientific_mcp(tools)
    contract = tools.get("igem.m2.screen_structure").metadata()
    assert "metrics" in contract["input_schema"]["properties"]
    engine = WorkflowEngine(WorkflowStore(tmp_path / "ledger.sqlite"), tools, tmp_path / "artifacts")
    workflow = Workflow(id="m2", name="m2", nodes=[WorkflowNode(id="screen", label="screen", tool_id="igem.m2.screen_structure", inputs={"metrics": LiteralInput(value={"candidate_id": "generic", "core_ca_rmsd_angstrom": 0.5, "sasa_retention": 0.9, "pocket_rmsd_angstrom": 1.0, "mean_plddt": 85.0, "clash_count": 0, "clash_cutoff_angstrom": 2.5})})])
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))
    assert result["status"] == "succeeded", result["nodes"]
    assert result["nodes"][0]["output"]["result"]["verdict"] == "pass"


def test_run_rejects_modified_import_bytes(tmp_path: Path):
    source = tmp_path / "sequence.fasta"
    source.write_bytes(b">p\nMAGSGS\n")
    project = Project(id="p", name="p", files=[{"name": "sequence.fasta", "path": str(source), "sha256": sha256(source.read_bytes()).hexdigest()}])
    tools = builtin_tools()
    engine = WorkflowEngine(WorkflowStore(tmp_path / "ledger.sqlite"), tools, tmp_path / "artifacts")
    workflow = Workflow(id="mcp", name="real stdio", nodes=[WorkflowNode(id="gather", label="gather", tool_id="workflow.gather", inputs={"results": LiteralInput(value=[])})])
    run_id = engine.create(project, workflow)
    source.write_bytes(b">p\nAAA\n")
    with pytest.raises(ValueError, match="input_artifact_hash_mismatch"):
        engine.run(run_id)


@pytest.mark.parametrize("field,value", [("phi", float("nan")), ("residual_tolerance", float("inf"))])
def test_pathway_rejects_nonfinite_parameters(field, value):
    with pytest.raises(ValueError):
        Pathway.model_validate({**pathway_payload(), field: value})


def test_resume_rejects_corrupted_successful_results(tmp_path: Path):
    engine = WorkflowEngine(WorkflowStore(tmp_path / "ledger.sqlite"), builtin_tools(), tmp_path / "artifacts")
    workflow = Workflow(id="g", name="g", nodes=[WorkflowNode(id="g", label="g", tool_id="workflow.gather", inputs={"results": LiteralInput(value=[])})])
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))
    Path(result["artifacts"][0]["path"]).write_text("{}")
    with pytest.raises(ValueError, match="output_artifact_hash_mismatch"):
        engine.verify_snapshot(engine.store.run(result["id"]))
