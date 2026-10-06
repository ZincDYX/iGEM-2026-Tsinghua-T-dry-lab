"""Software dependency closure oracle; no scientific handler is invoked."""
from hashlib import sha256
from dataclasses import replace
from pathlib import Path
import json
import subprocess
import sys
import pytest

from test_r6_input_boundaries import api, bundle
from igem_drylab.workflow.models import Contract, Workflow, WorkflowNode
from igem_drylab.workflow.scientific_project import ScientificProject
from igem_drylab.workflow.tools import ToolDefinition, WorkflowTools


class Empty(Contract):
    pass


def fixture_tool():
    return ToolDefinition("fixture.paths", "File identity fixture", "Not biology", "1", Empty,
                          lambda v, c: {"fixture": True}, "software_fixture")


def prepared(tmp_path, entry="configs/project.yaml", request=None):
    app, client = api(tmp_path)
    app.state.workflow_engine.tools.register(fixture_tool())
    response = client.post("/api/platform/scientific-projects/upload-preview", json=request or bundle(entry))
    assert response.status_code == 200, response.text
    saved = client.post("/api/platform/projects", json={"project": {"id": "original", "name": "Fixture", "scientific_project": response.json()["scientific_project"]}})
    assert saved.status_code == 200, saved.text
    project = app.state.platform_store.project("original")
    run_id = app.state.workflow_engine.create(project, Workflow(id="fixture", name="No computation", nodes=[WorkflowNode(id="files", label="files", tool_id="fixture.paths")]))
    return app, client, project, run_id


@pytest.mark.parametrize("entry", ["project.yaml", "configs/project.yaml"])
def test_iteration_keeps_original_m2_relative_graph_bytes_and_new_grants(tmp_path, entry):
    app, client, original, run_id = prepared(tmp_path, entry)
    store = app.state.platform_store
    frozen = store.run(run_id)
    original_bytes = {item.path: item.path.read_bytes() for item in ScientificProject.model_validate(original.scientific_project).evidence_files}
    response = client.post(f"/api/platform/runs/{run_id}/iteration")
    assert response.status_code == 200, response.text
    public = response.json()["project"]
    private = store.project(public["id"])
    science = ScientificProject.model_validate(private.scientific_project)
    science.verify()
    new_metrics = science.config.stages.m2_fusion.structure_metrics_file
    old_metrics = ScientificProject.model_validate(original.scientific_project).config.stages.m2_fusion.structure_metrics_file
    assert new_metrics.read_bytes() == old_metrics.read_bytes()
    for relative in ("../structures/model.pdb", "../structures/ref.pdb", "../geometry/input.json", "../geometry/sasa.json"):
        target = (new_metrics.parent / relative).resolve()
        assert target.read_bytes() == (old_metrics.parent / relative).resolve().read_bytes()
        assert target in {item.path for item in science.evidence_files}
    assert client.get(f"/api/platform/projects/{private.id}/precheck").status_code == 200
    assert client.post("/api/platform/projects", json={"project": public, "expected_revision": 1}).status_code == 200
    for item in public["scientific_project"]["evidence_files"]:
        download = client.get(f"/api/platform/files/{item['id']}?project_id={private.id}")
        assert download.status_code == 200
        assert sha256(download.content).hexdigest() == item["sha256"]
        assert client.get(f"/api/platform/files/{item['id']}?project_id=original").status_code == 403
    assert store.run(run_id)["snapshot_hash"] == frozen["snapshot_hash"]
    assert store.run(run_id)["snapshot"] == frozen["snapshot"]
    assert all(path.read_bytes() == raw for path, raw in original_bytes.items())
    # The copied graph must survive another generation, not only one rename.
    second_run = app.state.workflow_engine.create(store.project(private.id), Workflow(id="fixture2", name="No computation", nodes=[WorkflowNode(id="files", label="files", tool_id="fixture.paths")]))
    again = client.post(f"/api/platform/runs/{second_run}/iteration")
    assert again.status_code == 200, again.text
    ScientificProject.model_validate(store.project(again.json()["project"]["id"]).scientific_project).verify()


@pytest.mark.parametrize("kind", ["missing", "tampered", "transaction_failure", "copy_failure"])
def test_failed_iteration_never_publishes_project_or_file_grants(tmp_path, monkeypatch, kind):
    app, client, original, run_id = prepared(tmp_path)
    store = app.state.platform_store
    with store.connection() as db:
        before = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("projects", "file_assets", "scientific_bundles")}
    directories = set((tmp_path / "imports").iterdir())
    if kind in {"missing", "tampered"}:
        path = ScientificProject.model_validate(original.scientific_project).config.stages.m2_fusion.structure_metrics_file.parent.parent / "structures/model.pdb"
        if kind == "missing":
            path.unlink()  # Only the owned software fixture, never original user data.
        else:
            path.write_bytes(b"CHANGED_SOFTWARE_FIXTURE")
    elif kind == "copy_failure":
        real_write = Path.write_bytes
        def fail_owned_copy(path, raw):
            if any(part.startswith(".iteration-") for part in path.parts):
                raise OSError("SOFTWARE_FIXTURE copy failed")
            return real_write(path, raw)
        monkeypatch.setattr(Path, "write_bytes", fail_owned_copy)
    else:
        boundary = app.state.disclosure
        real = boundary.project
        def reject_after_grants(project, **kwargs):
            real(project, **kwargs)
            raise ValueError("SOFTWARE_FIXTURE after grant insertion")
        monkeypatch.setattr(boundary, "project", reject_after_grants)
    response = client.post(f"/api/platform/runs/{run_id}/iteration")
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "iteration_dependency_graph_invalid"
    assert str(tmp_path) not in response.text
    with store.connection() as db:
        assert before == {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert set((tmp_path / "imports").iterdir()) == directories


def test_same_basename_in_distinct_dependencies_never_collides(tmp_path):
    request = bundle()
    for item in request["files"]:
        if item["filename"] == "structures/ref.pdb":
            item.update(filename="reference/model.pdb", content="DISTINCT_REFERENCE_FIXTURE")
        if item["filename"] == "metrics/m2.json":
            metrics = json.loads(item["content"])
            metrics[0]["reference_artifact_path"] = "../reference/model.pdb"
            item["content"] = json.dumps(metrics)
    app, client, original, run_id = prepared(tmp_path, request=request)
    response = client.post(f"/api/platform/runs/{run_id}/iteration")
    assert response.status_code == 200, response.text
    science = ScientificProject.model_validate(app.state.platform_store.project(response.json()["project"]["id"]).scientific_project)
    root = science.config.stages.m2_fusion.structure_metrics_file.parent.parent
    assert (root / "structures/model.pdb").read_bytes() == b"SOFTWARE_FIXTURE"
    assert (root / "reference/model.pdb").read_bytes() == b"DISTINCT_REFERENCE_FIXTURE"
    science.verify()


def test_changed_tool_requires_new_plan_but_does_not_block_input_only_iteration(tmp_path):
    app, client, _, run_id = prepared(tmp_path)
    engine = app.state.workflow_engine
    engine.tools = WorkflowTools()
    engine.tools.register(replace(fixture_tool(), version="changed-fixture-version"))
    with pytest.raises(ValueError, match="tool_changed_since_snapshot"):
        engine.verify_snapshot(app.state.platform_store.run(run_id))
    response = client.post(f"/api/platform/runs/{run_id}/iteration")
    assert response.status_code == 200, response.text
    assert response.json()["reuse_supported"] is False
    assert app.state.platform_store.runs(response.json()["project"]["id"]) == []


def test_process_exit_during_writer_transaction_never_grants_half_project(tmp_path):
    app, _, _, run_id = prepared(tmp_path)
    store = app.state.platform_store
    with store.connection() as db:
        before = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("projects", "file_assets", "scientific_bundles")}
    script = """
import os, sys
from pathlib import Path
from test_r6_input_boundaries import api
from test_r7_iteration import fixture_tool
app, client = api(Path(sys.argv[1]))
app.state.workflow_engine.tools.register(fixture_tool())
boundary = app.state.disclosure
real = boundary.project
def exit_after_grants(project, **kwargs):
    real(project, **kwargs)
    os._exit(75)
boundary.project = exit_after_grants
client.post('/api/platform/runs/' + sys.argv[2] + '/iteration')
"""
    import os
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=os.pathsep.join([str(Path(__file__).parent), str(Path(__file__).parent.parent / "src")]))
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), run_id], env=environment, capture_output=True, timeout=45)
    assert result.returncode == 75, result.stderr.decode(errors="replace")
    with store.connection() as db:
        assert before == {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    # A crash may retain a private orphan copy, never a published project/grant.
    assert len(store.runs("original")) == 1
