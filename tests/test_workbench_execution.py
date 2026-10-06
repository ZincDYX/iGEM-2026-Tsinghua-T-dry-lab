"""Blocking software handlers/SQLite oracles, no biological computation."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Event, Lock
from time import sleep

import pytest

from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Contract, ExecutionPolicy, LiteralInput, NodeInput, Project, ProjectInput, Workflow, WorkflowNode, WorkflowError
from igem_drylab.workflow.scientific_project import ScientificProject, StageInput, bound_predecessor, validate_stage_bindings
from igem_drylab.workflow.store import WorkflowStore, canonical, plan_binding
from igem_drylab.workflow.tools import NodeContext, ToolDefinition, WorkflowTools


class Empty(Contract):
    pass


def engine(tmp_path, handler, *, max_workers=2, resource="cpu", idempotent=True):
    tools = WorkflowTools()
    tools.register(ToolDefinition("fixture", "fixture", "software oracle", "1", Empty, handler, "software_fixture",resource=resource,idempotent=idempotent))
    return WorkflowEngine(WorkflowStore(tmp_path / "ledger.sqlite"),tools,tmp_path / "artifacts",max_workers=max_workers)


def graph(count=2, **policy):
    return Workflow(id="fixture",name="fixture",nodes=[WorkflowNode(id=f"n{i}",label=f"n{i}",tool_id="fixture") for i in range(count)],execution_policy=ExecutionPolicy(**policy))


@pytest.mark.parametrize("resource,expected_peak", [("cpu",2),("gpu",1)])
def test_multiple_runs_share_actual_global_task_and_gpu_budget(tmp_path, resource, expected_peak):
    release, reached, lock = Event(), Event(), Lock()
    active = peak = calls = 0
    def handler(payload, context):
        nonlocal active,peak,calls
        with lock:
            active += 1; calls += 1; peak = max(peak,active)
            if active == expected_peak: reached.set()
        assert release.wait(5), "fixture not released"
        with lock: active -= 1
        return {"kind":"software_fixture"}
    runtime = engine(tmp_path,handler,resource=resource)
    ids = [runtime.create(Project(id=f"p{i}",name="fixture"),graph()) for i in range(2)]
    with ThreadPoolExecutor(max_workers=2) as controllers:
        futures = [controllers.submit(runtime.run,run_id) for run_id in ids]
        try:
            assert reached.wait(3)
            sleep(.1)
            assert peak == expected_peak
            assert runtime.budget.state()["active_tasks"] <= 2
        finally: release.set()
        assert all(f.result(timeout=5)["status"] == "succeeded" for f in futures)
    assert calls == 4 and peak == expected_peak


def test_single_stage_and_checkpoint_resume_are_real_and_do_not_reexecute_success(tmp_path):
    calls = []
    runtime = engine(tmp_path,lambda value,context: calls.append(context.node_id) or {"kind":"software_fixture"})
    workflow = graph(3,max_completed_stages=1,checkpoints_before=["n1"])
    run_id = runtime.create(Project(id="p",name="fixture"),workflow)
    assert runtime.run(run_id)["status"] == "paused" and calls == ["n0"]
    runtime.store.clear_control(run_id)
    assert runtime.run(run_id)["status"] == "paused" and calls == ["n0"]
    runtime.store.clear_control(run_id)
    assert runtime.run(run_id)["status"] == "paused" and calls == ["n0","n1"]
    runtime.store.clear_control(run_id)
    assert runtime.run(run_id)["status"] == "succeeded" and calls == ["n0","n1","n2"]


def test_cancel_waits_for_actual_handler_and_does_not_publish_late_output(tmp_path):
    entered,release = Event(),Event()
    def handler(value,context):
        entered.set(); assert release.wait(5)
        return {"kind":"complete_software_fixture"}
    runtime = engine(tmp_path,handler,max_workers=1)
    run_id = runtime.create(Project(id="p",name="fixture"),graph(1))
    with ThreadPoolExecutor(max_workers=1) as controller:
        future = controller.submit(runtime.run,run_id)
        assert entered.wait(3)
        runtime.store.control(run_id,"cancel")
        assert runtime.store.execution_state(run_id)["status"] == "running"
        assert not future.done()
        release.set()
        result = future.result(timeout=5)
    assert result["status"] == "cancelled" and result["artifacts"] == []
    assert result["nodes"][0]["status"] == "interrupted"


def test_confirmed_request_is_idempotent_and_policy_changes_require_new_review(tmp_path):
    runtime = engine(tmp_path,lambda value,context:{"kind":"fixture"})
    project = runtime.store.save_project(Project(id="p",name="fixture"))
    workflow = graph(1)
    binding = plan_binding(project,workflow)
    first = runtime.create_confirmed(binding,workflow,"same-task")
    assert runtime.create_confirmed(binding,workflow,"same-task") == first
    assert len(runtime.store.runs()) == 1
    changed = workflow.model_copy(deep=True)
    changed.execution_policy.checkpoints_after = ["n0"]
    with pytest.raises(WorkflowError,match="changed_regenerate_and_review"):
        runtime.create_confirmed(binding,changed,"same-task")


def test_formal_graph_rejects_literal_records_and_wrong_parent_before_invocation():
    workflow = Workflow(id="bad",name="bad",nodes=[WorkflowNode(id="m4",label="m4",tool_id="project.m4",inputs={"project":ProjectInput(path=["scientific_project"]),"upstream_records":LiteralInput(value=[{"evidence_ready":True}])})])
    with pytest.raises(WorkflowError,match="registered_upstream"):
        validate_stage_bindings(workflow)


@pytest.mark.parametrize("mutation", ["records","artifact_hash","project","snapshot","schema","stage"])
def test_registered_parent_content_and_identity_not_client_flags_are_authoritative(tmp_path, mutation):
    # A typed config is constructed but never verified/read/run. Rows are not
    # scientific model records and cannot be offered as biological evidence.
    science = ScientificProject(config=ProjectConfig.model_validate({"run":{"id":"software-fixture"},"inputs":{"protein_fasta":"not-read-software-fixture.fasta","enzymes":[],"scaffolds":[],"linkers":[]}}),evidence_files=[])
    identity = {"artifact_id":"fixture-parent","sha256":"a"*64}
    parent = {**identity,"run_id":"run","project_id":"project","snapshot_hash":"b"*64,
        "output":{"schema_version":"scientific-stage-v1","module":"m3","records":[{"kind":"software_fixture"}],"resource_artifacts":[]}}
    payload = StageInput(project=science,upstream_result=identity)
    context = NodeContext("run","m4",tmp_path,upstream_results=(parent,),project_id="project",snapshot_sha256="b"*64,
        scientific_project_sha256=sha256(canonical(science.model_dump(mode="json")).encode()).hexdigest())
    assert bound_predecessor(payload,context,"m4") == [{"kind":"software_fixture"}]
    if mutation == "records": payload.upstream_records = [{"evidence_ready":True}]
    elif mutation == "artifact_hash": payload.upstream_result = {**identity,"sha256":"c"*64}
    elif mutation == "project": parent["project_id"] = "other-project"
    elif mutation == "snapshot": parent["snapshot_hash"] = "d"*64
    elif mutation == "schema": parent["output"]["schema_version"] = "unknown"
    elif mutation == "stage": parent["output"]["module"] = "m2"
    with pytest.raises(WorkflowError): bound_predecessor(payload,context,"m4")


def test_node_record_requires_registered_successful_artifact_bytes(tmp_path):
    runtime = engine(tmp_path,lambda value,context:{"kind":"software_fixture"})
    run_id = runtime.create(Project(id="p",name="fixture"),graph(1))
    result = runtime.run(run_id)
    parent = runtime.store.verified_upstream(run_id,["n0"])[0]
    assert parent["output"] == {"kind":"software_fixture"}
    from pathlib import Path
    Path(result["artifacts"][0]["path"]).write_text('{"forged":true}',encoding="utf-8")
    with pytest.raises(WorkflowError,match="hash_mismatch"):
        runtime.store.verified_upstream(run_id,["n0"])
