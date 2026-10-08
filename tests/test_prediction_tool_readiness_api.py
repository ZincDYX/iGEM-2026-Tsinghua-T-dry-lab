from fastapi.testclient import TestClient

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import Project


def test_private_backend_tools_bind_new_project_but_do_not_leak_settings(tmp_path):
    app = create_app(data_dir=tmp_path, session_token="owned_protocol_fixture", discover_tools=False,
        runtime_tools={"seg": {"enabled": True, "mode": "external", "command": "PRIVATE_EXECUTABLE_NO_FRONTEND",
            "verified_version": "PROTOCOL_VERSION", "extra": {"api_key": "PRIVATE_KEY_NOT_PUBLIC"}}})
    with TestClient(app) as client:
        headers = {"X-FusionLab-Token": "owned_protocol_fixture"}
        project = Project(id="p", name="PROTOCOL_FIXTURE").model_dump(mode="json")
        response = client.post("/api/platform/projects", json={"project": project, "expected_revision": None}, headers=headers)
        assert response.status_code == 200
        assert response.json()["runtime_profile_ref"] is None
        assert app.state.platform_store.project("p").runtime_profile_ref == "backend-configured-tools"
        rows = client.get("/api/platform/projects/p/prediction-tools", headers=headers)
        assert rows.status_code == 200
        assert len(rows.json()) == 3
        assert rows.json()[1]["version"] == "PROTOCOL_VERSION"
        assert "PRIVATE_" not in rows.text
        assert rows.json()[1]["status"] == "not_configured"  # Presence of configuration != callable tool.
        assert client.get("/api/platform/projects/p/prediction-tools").status_code == 401
