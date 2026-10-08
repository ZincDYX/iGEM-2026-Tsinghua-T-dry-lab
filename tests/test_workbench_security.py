"""Software-only fake-secret oracles; no scientific run or real credential."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.disclosure import DisclosureBoundary
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Contract, LiteralInput, Project, Workflow, WorkflowNode, WorkflowError
from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import ToolDefinition, WorkflowTools


FAKE_SECRET = "SOFTWARE_FIXTURE_NOT_A_CREDENTIAL_20261006"


def client(tmp_path):
    app = create_app(data_dir=tmp_path, session_token="fixture-desktop-session", discover_tools=False)
    return app, TestClient(app, headers={"X-FusionLab-Token": "fixture-desktop-session"})


def test_production_authentication_is_required_and_query_tokens_do_not_authenticate(tmp_path):
    with pytest.raises(ValueError, match="requires_private_session_token"):
        create_app(data_dir=tmp_path, discover_tools=False)
    app, authenticated = client(tmp_path)
    anonymous = TestClient(app)
    assert anonymous.get("/api/platform/info").status_code == 401
    assert anonymous.get("/api/platform/artifacts/fake?token=fixture-desktop-session").status_code == 401
    info = authenticated.get("/api/platform/info")
    assert info.status_code == 200
    assert "data_dir" not in info.json()
    assert info.json()["protocol_version"] == "2"
    assert info.json()["remote_desktop_authenticated_session"] is True


def test_http_error_and_import_views_do_not_contain_private_paths_or_validation_input(tmp_path):
    app, api = client(tmp_path)
    boundary = app.state.disclosure
    boundary.register_private(FAKE_SECRET)
    rejected = api.post("/api/platform/scientific-projects/preview", json={"config_path": str(tmp_path.parent / "private" / "secret.yaml")})
    assert rejected.status_code == 403
    assert str(tmp_path.parent) not in rejected.text
    malformed = api.post("/api/platform/projects", json={"project": {"id": "x", "name": FAKE_SECRET, "unknown": FAKE_SECRET}})
    assert malformed.status_code == 422 and FAKE_SECRET not in malformed.text
    preview = api.post("/api/platform/imports/preview", json={"filename": "fixture.csv", "content": "id,value\nx,not-scientific\n"})
    assert preview.status_code == 200
    assert preview.json()["file"]["path"].startswith("asset:")
    assert str(tmp_path) not in preview.text
    assert api.post("/api/platform/projects", json={"project": {"id": "p", "name": FAKE_SECRET}}).status_code == 403


def test_logical_file_identity_cannot_be_rebound_to_other_project_or_mutated(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    boundary = DisclosureBoundary(store)
    source = tmp_path / "fixture.txt"
    source.write_text("software fixture", encoding="utf-8")
    asset = boundary.asset(source, project_id="project-a")
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        boundary.resolve_asset(asset["id"], "project-b")
    source.write_text("modified fixture", encoding="utf-8")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        boundary.resolve_asset(asset["id"], "project-a")


@pytest.mark.parametrize("payload", [{"value": FAKE_SECRET}, {"value": "/private/software-fixture/settings.json"}])
def test_sensitive_handler_output_is_not_published_as_success_or_downloadable_artifact(tmp_path, payload):
    class Empty(Contract):
        pass
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    tools = WorkflowTools()
    tools.register(ToolDefinition("fixture.echo", "fixture", "software oracle", "1", Empty, lambda value, context: payload, "software_fixture"))
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts")
    engine.disclosure.register_private(FAKE_SECRET)
    workflow = Workflow(id="fixture", name="fixture", nodes=[WorkflowNode(id="echo", label="echo", tool_id="fixture.echo")])
    result = engine.run(engine.create(Project(id="fixture", name="fixture"), workflow))
    assert result["status"] == "failed" and result["artifacts"] == []
    public = engine.disclosure.run(result)
    assert FAKE_SECRET not in json.dumps(public) and "/private/" not in json.dumps(public)
    assert public["nodes"][0]["error"]["diagnostic_id"]


def test_private_runtime_profile_has_separate_identity_and_is_not_a_project_payload(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    profile = RuntimeProfiles(store)
    identity = profile.install("fixture-runtime", {"unused": {"extra": {"api_key": FAKE_SECRET}}})
    assert set(identity) == {"id", "revision", "hash"} and FAKE_SECRET not in json.dumps(identity)
    boundary = DisclosureBoundary(store)
    public = boundary.project(Project(id="p", name="p", runtime_profile_ref="fixture-runtime"))
    assert FAKE_SECRET not in json.dumps(public)
    with pytest.raises(WorkflowError, match="disclosure_quarantined"):
        boundary.check({"value": FAKE_SECRET})
    assert profile.get("fixture-runtime")[1]["unused"]["extra"]["api_key"] == FAKE_SECRET
