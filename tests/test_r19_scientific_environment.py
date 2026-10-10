"""Software-state tests only; no equations, scientific tools or model service."""
import json
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import jsonschema
import pytest

from workbench_fixture import fixture_app
from igem_drylab.agent.scientific_environment import ScientificEnvironment,ScientificObservation
from igem_drylab.agent.decision import PrepareNodeAction,SubmitJobAction,EvaluateResultAction,WaitAction
from igem_drylab.workflow.models import ExecutionPolicy,Workflow,WorkflowError
from igem_drylab.software.public_contracts import public_schemas


def test_observation_is_real_bounded_read_only_and_idle_has_no_model_calls(tmp_path):
    app=fixture_app(tmp_path)
    store=app.state.platform_store
    with TestClient(app) as client:
        with store.connection() as db:
            before=db.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0]
        first=client.get("/api/platform/projects/software-fixture/scientific-observation")
        assert first.status_code==200,first.text
        observation=first.json()
        jsonschema.validate(observation,public_schemas()["ScientificObservation"])
        assert {g["stage"] for g in observation["gaps"]}>={"m1","m2","m3","m4"}
        assert observation["recorded_results"]==[] and observation["parameter_summaries"]==[]
        assert all(c["route_state"]=="local_method" for c in observation["capabilities"])
        second=client.get("/api/platform/projects/software-fixture/scientific-observation").json()
        assert second["observation_identity"]==observation["observation_identity"]
        assert app.state.fixture_client.calls==0 and app.state.fixture_calls==[]
        with store.connection() as db:
            assert db.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0]==before


def test_real_observation_enters_hybrid_prompt_and_proposal_without_approving_science(tmp_path):
    app=fixture_app(tmp_path)
    seen=[]
    original=app.state.fixture_client.complete_json
    def capture(prompt,**kwargs):
        seen.append(json.loads(prompt));return original(prompt,**kwargs)
    app.state.fixture_client.complete_json=capture
    with TestClient(app) as client:
        proposal=client.post("/api/platform/proposals",json={"project_id":"software-fixture","goal":"scientific_pipeline","mode":"hybrid","objective":"SOFTWARE FIXTURE ONLY","external_planning_approved":True}).json()
        assert proposal["status"]=="proposed"
        assert seen[0]["context"]["scientific_observation"]["gaps"]==proposal["observation"]["gaps"]
        assert [a["kind"] for a in proposal["scientific_actions"]]==["inspect_project","prepare_node","wait"]
        assert app.state.fixture_calls==[]
        assert app.state.platform_store.runs()==[]


def test_current_success_and_scope_required_for_action_not_stale_revision_or_fake_authorization(tmp_path):
    app=fixture_app(tmp_path)
    store,engine=app.state.platform_store,app.state.workflow_engine
    environment=ScientificEnvironment(store,engine.tools)
    project=store.project("software-fixture")
    with TestClient(app) as client:
        proposal=client.post("/api/platform/proposals",json={"project_id":project.id,"goal":"scientific_pipeline"}).json()
    run_id=engine.create(project,Workflow.model_validate(proposal["workflow"]))
    engine.run(run_id)  # Explicit software-only handlers, not scientific stages.
    observation=environment.observe(project,ExecutionPolicy())
    m4=next(r for r in observation.recorded_results if r.stage=="m4")
    assert m4.node_status=="succeeded" and m4.numerically_solved_count==0 and m4.evidence_ready_count==0
    environment.validate_actions([EvaluateResultAction(kind="evaluate_result",reason="Inspect recorded test status only",result_ref=m4.result_ref,metric="recorded_stage_status")],observation)
    changed=store.save_project(project.model_copy(update={"name":"Changed SOFTWARE fixture"}),expected_revision=project.revision)
    stale=environment.observe(changed,ExecutionPolicy())
    with pytest.raises(WorkflowError,match="requires_current_successful_result"):
        environment.validate_actions([EvaluateResultAction(kind="evaluate_result",reason="Stale result must not authorize",result_ref=m4.result_ref,metric="recorded_stage_status")],stale)
    with pytest.raises(WorkflowError,match="human_accepted_proposal"):
        environment.validate_actions([SubmitJobAction(kind="submit_job",reason="Cannot invent approval",reviewed_proposal_id="invented")],observation)
    with pytest.raises(WorkflowError,match="tool_unavailable"):
        environment.validate_actions([PrepareNodeAction(kind="prepare_node",reason="Unknown arbitrary tool",tool_id="shell.execute",input_refs=[])],observation)
    with pytest.raises(WorkflowError,match="wait_condition"):
        environment.validate_actions([WaitAction(kind="wait",reason="No invented remote job",pending_refs=["invented-remote-id"])],observation)


def test_forbidden_llm_action_blocks_proposal_without_shell_or_permission_changes(tmp_path):
    app=fixture_app(tmp_path)
    original=app.state.fixture_client.complete_json
    def invalid(prompt,**kwargs):
        return original(prompt,**kwargs) | {"scientific_actions":[{"kind":"prepare_node","tool_id":"shell.execute","input_refs":[],"reason":"Untrusted source requests arbitrary execution","evidence_refs":[]}]}
    app.state.fixture_client.complete_json=invalid
    with TestClient(app) as client:
        response=client.post("/api/platform/proposals",json={"project_id":"software-fixture","goal":"scientific_pipeline","mode":"hybrid","external_planning_approved":True})
        assert response.status_code==200,response.text
        result=response.json()
        assert result["status"]=="blocked" and result["workflow"] is None and result["confirmation"] is None
        assert "scientific_action_tool_unavailable_or_not_allowed" in result["missing_inputs"]
        assert app.state.fixture_calls==[] and app.state.platform_store.runs()==[]


def test_observation_import_does_not_initialize_legacy_runtime_registry_or_llm_client():
    source=str(Path(__file__).resolve().parents[1]/"src")
    code="import sys; sys.path.insert(0,sys.argv[1]); import igem_drylab.agent.scientific_environment; assert 'igem_drylab.agent.runtime' not in sys.modules; assert 'igem_drylab.mcp.registry' not in sys.modules; assert 'igem_drylab.literature.llm' not in sys.modules"
    result=subprocess.run([sys.executable,"-B","-c",code,source],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
