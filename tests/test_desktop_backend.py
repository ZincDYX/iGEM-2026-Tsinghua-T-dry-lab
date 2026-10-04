import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep

from fastapi.testclient import TestClient
import requests

from igem_drylab.software.dashboard import create_app


def test_desktop_session_token_is_required(tmp_path: Path):
    client = TestClient(create_app(data_dir=tmp_path, session_token="test-session"))
    assert client.get("/api/platform/info").status_code == 401
    assert client.get("/api/platform/info?token=test-session").status_code == 401
    assert client.get("/api/platform/info", headers={"X-FusionLab-Token": "test-session"}).status_code == 200
    response = client.options("/api/platform/info", headers={"Origin": "http://tauri.localhost", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "X-FusionLab-Token"})
    assert response.status_code == 200


def test_real_desktop_python_process_uses_random_loopback_port(tmp_path: Path):
    ready = tmp_path / "ready.json"
    env = {**os.environ, "FUSIONLAB_SESSION_TOKEN": "process-test-token"}
    process = subprocess.Popen([sys.executable, "-m", "igem_drylab.software.desktop_backend", "--data-dir", str(tmp_path), "--ready-file", str(ready)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = monotonic() + 15
        while not ready.exists() and process.poll() is None and monotonic() < deadline:
            sleep(0.05)
        assert ready.exists(), "Desktop backend did not start"
        url = json.loads(ready.read_text())["url"]
        assert url.startswith("http://127.0.0.1:")
        assert "token" not in ready.read_text()
        assert requests.get(url + "/api/platform/info", timeout=5).status_code == 401
        assert requests.get(url + "/api/platform/projects", headers={"X-FusionLab-Token": "process-test-token"}, timeout=5).json() == []
    finally:
        process.kill()
        process.communicate(timeout=5)
