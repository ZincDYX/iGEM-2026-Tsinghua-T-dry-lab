from __future__ import annotations

from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from igem_drylab.software.dashboard import create_app


def test_import_confirm_execute_and_reopen_local_database(tmp_path: Path) -> None:
    client = TestClient(create_app(data_dir=tmp_path))
    project = client.post("/api/platform/projects", json={"project": {"id": "p", "name": "Generic fusion"}}).json()
    preview = client.post("/api/platform/imports/preview", json={"filename": "fusion.fasta", "content": ">enzyme-tag\nMAGSGS\n>scaffold\nMKKGGSS\n"}).json()
    assert client.get("/api/platform/projects").json()[0]["sequences"] == []
    project.update(preview["patch"])
    project["files"] = [preview["file"]]
    response = client.post("/api/platform/projects", json={"project": project, "expected_revision": 1})
    assert response.status_code == 200
    plan = client.post("/api/platform/plans", json={"project_id": "p", "goal": "fusion_screen"}).json()["workflow"]
    response = client.post("/api/platform/runs", json={"project_id": "p", "workflow": plan})
    assert response.status_code == 202
    run_id = response.json()["id"]
    for _ in range(100):
        run = client.get(f"/api/platform/runs/{run_id}").json()
        if run["status"] in {"succeeded", "failed"}:
            break
        sleep(0.02)
    assert run["status"] == "succeeded", run
    assert len(run["artifacts"]) == 4
    reopened = TestClient(create_app(data_dir=tmp_path))
    assert reopened.get(f"/api/platform/runs/{run_id}").json()["snapshot_hash"] == run["snapshot_hash"]
    assert reopened.get(f"/api/platform/artifacts/{run['artifacts'][0]['id']}").status_code == 200
    assert reopened.post("/api/platform/projects", json={"project": project, "expected_revision": 1}).status_code == 409


def test_duplicate_fasta_and_invalid_pathway_are_rejected(tmp_path: Path) -> None:
    client = TestClient(create_app(data_dir=tmp_path))
    assert client.post("/api/platform/imports/preview", json={"filename": "duplicate.fa", "content": ">x\nMAG\n>x\nMSG\n"}).status_code == 422
    assert client.post("/api/platform/imports/preview", json={"filename": "invalid.json", "content": "{\"id\": \"fake\"}"}).status_code == 422
