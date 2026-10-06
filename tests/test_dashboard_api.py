from __future__ import annotations

from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from igem_drylab.mcp.types import McpToolResult
from igem_drylab.software.dashboard import create_app


class StubRegistry:
    def __init__(self, result: McpToolResult) -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call(self, name: str, arguments: dict[str, object]) -> McpToolResult:
        self.calls.append((name, arguments))
        return self.result


def _eventually(client: TestClient, run_id: str) -> dict[str, object]:
    for _ in range(20):
        payload = client.get(f"/api/dashboard/runs/{run_id}").json()
        if payload["status"] in {"succeeded", "failed", "unavailable"}:
            return payload
        sleep(0.01)
    raise AssertionError("Dashboard run did not finish")


def test_dashboard_returns_real_m0_m5_dag_contract():
    client = TestClient(create_app(StubRegistry(McpToolResult.ok({"ok": True})), deployment_mode="development"))
    payload = client.get("/api/dashboard/dag").json()
    assert [item["id"] for item in payload] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    assert payload[0]["run_available"] is True
    assert payload[1]["run_available"] is False
    assert "standalone M1" in payload[1]["unavailable_reason"]


def test_dashboard_dispatches_m0_to_existing_registry_tool():
    registry = StubRegistry(McpToolResult.ok({"ok": True, "run_id": "demo"}))
    client = TestClient(create_app(registry, deployment_mode="development"))
    response = client.post("/api/dashboard/runs", json={"module_id": "m0", "config_path": "configs/m1_m4_example.yaml"})
    final = _eventually(client, response.json()["run_id"])
    assert final["status"] == "succeeded"
    assert registry.calls[0][0] == "igem.pipeline.validate"
    assert Path(str(registry.calls[0][1]["config_path"])).as_posix() == "configs/m1_m4_example.yaml"
    assert any(entry["status"] == "running" for entry in final["logs"])


def test_dashboard_m0_runs_actual_registry_validation():
    client = TestClient(create_app(deployment_mode="development"))
    response = client.post("/api/dashboard/runs", json={"module_id": "m0", "config_path": "configs/m1_m4_example.yaml"})
    final = _eventually(client, response.json()["run_id"])
    assert final["status"] == "succeeded"
    assert final["result"]["run_id"] == "m1-m4-demo"


def test_dashboard_returns_structured_runtime_failure():
    registry = StubRegistry(McpToolResult.error("missing reviewed parameters", error_type="insufficient_data"))
    client = TestClient(create_app(registry, deployment_mode="development"))
    response = client.post("/api/dashboard/runs", json={"module_id": "m4", "config_path": "configs/m1_m4_real_scoring_example.yaml"})
    final = _eventually(client, response.json()["run_id"])
    assert final["status"] == "failed"
    assert final["error"] == {"code": "insufficient_data", "message": "missing reviewed parameters"}
    assert registry.calls[0][0] == "igem.pipeline.run_stage"


def test_dashboard_honestly_marks_unavailable_isolated_module():
    client = TestClient(create_app(StubRegistry(McpToolResult.ok({"ok": True})), deployment_mode="development"))
    response = client.post("/api/dashboard/runs", json={"module_id": "m2", "config_path": "configs/m1_m4_example.yaml"})
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "unavailable"
    assert "No standalone M2" in payload["logs"][-1]["message"]
