"""Pagination, query plans and lock-race software oracles; no science runs."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import json

import pytest
from fastapi.testclient import TestClient

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import Project, Workflow, WorkflowNode, WorkflowError, NodeStatus
from igem_drylab.workflow.store import WorkflowStore, plan_binding


def test_status_and_project_lists_are_bounded_and_events_are_incremental(tmp_path):
    app = create_app(data_dir=tmp_path, deployment_mode="development", discover_tools=False)
    with TestClient(app) as client:
        store = app.state.platform_store
        store.save_project(Project(id="p",name="software_fixture",datasets=[{"rows":[{"unused_payload":"x"*500_000}]}]))
        workflow = Workflow(id="fixture",name="fixture",nodes=[WorkflowNode(id="n",label="n",tool_id="fixture")])
        run_id = store.create_run({"project":store.project("p").model_dump(mode="json"),"workflow":workflow.model_dump(mode="json"),"tools":{},"environment":{}})
        store.set_node(run_id,"n",NodeStatus.succeeded,output={"schema_version":"scientific-stage-v2","module":"m1","records":[{"kind":"software_fixture","ordinal":i} for i in range(1000)]})
        summaries = client.get("/api/platform/project-summaries").json()
        assert summaries == [{"id":"p","name":"software_fixture","revision":1,"scientific":False,"sequence_count":0,
                              "scientific_sequence_count":None,"scientific_sequence_index_status":"not_attached"}]
        summary = client.get(f"/api/platform/runs/{run_id}/summary")
        assert summary.status_code == 200 and len(summary.content) < 3000
        assert "unused_payload" not in summary.text and '"records"' not in summary.text
        first = client.get(f"/api/platform/runs/{run_id}/events?limit=1").json()
        assert len(first["items"]) == 1 and first["has_more"]
        second = client.get(f"/api/platform/runs/{run_id}/events?after_seq={first['cursor']}").json()
        assert all(item["seq"] > first["cursor"] for item in second["items"])
        page = client.get(f"/api/platform/runs/{run_id}/nodes/n/result?offset=500&limit=2").json()
        assert page["total_records"] == 1000 and [row["ordinal"] for row in page["node"]["output"]["records"]] == [500,501]
        version = summary.json()["state_version"]
        store.control(run_id,"pause")
        assert client.get(f"/api/platform/runs/{run_id}/summary").json()["state_version"] > version
        assert client.get(f"/api/platform/runs/{run_id}/nodes/n/result?limit=101").status_code == 422


def test_snapshot_preparation_holds_no_writer_lock_and_rereads_approval(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    project = store.save_project(Project(id="p",name="fixture"))
    workflow = Workflow(id="fixture",name="fixture",nodes=[WorkflowNode(id="n",label="n",tool_id="fixture")])
    entered, release = Event(), Event()
    def prepare(value):
        entered.set()
        assert release.wait(3)
        return {"project":value.model_dump(mode="json"),"workflow":workflow.model_dump(mode="json"),"tools":{}}
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(store.create_confirmed_run,plan_binding(project,workflow),workflow,prepare)
        assert entered.wait(2)
        try:
            changed = store.save_project(project.model_copy(update={"name":"changed"}),expected_revision=1)
            assert changed.revision == 2
        finally: release.set()
        with pytest.raises(WorkflowError,match="changed_regenerate_and_review"): future.result(timeout=3)
    assert store.runs() == []


def test_representative_history_uses_indices_and_page_limits(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    workflow = Workflow(id="fixture",name="fixture",nodes=[WorkflowNode(id="n",label="n",tool_id="fixture")])
    run_id = store.create_run({"project":Project(id="p",name="fixture").model_dump(mode="json"),"workflow":workflow.model_dump(mode="json")})
    with store.connection() as db:
        db.executemany("INSERT INTO events(run_id,event,payload,timestamp) VALUES(?,?,?,?)",[(run_id,"fixture","{}","fixture-time") for _ in range(10000)])
        plans = [" ".join(str(part) for row in db.execute("EXPLAIN QUERY PLAN "+query,args) for part in row) for query,args in [
            ("SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT 100",(run_id,500)),
            ("SELECT * FROM artifacts WHERE run_id=?",(run_id,)),
            ("SELECT id FROM runs WHERE project_id=? ORDER BY created_at DESC LIMIT 20",("p",))]]
    assert "events_run_seq" in plans[0] and "artifacts_run" in plans[1] and "runs_project_time" in plans[2]
    assert len(store.runs("p",limit=1)) == 1 and store.runs("p",offset=1,limit=1) == []
