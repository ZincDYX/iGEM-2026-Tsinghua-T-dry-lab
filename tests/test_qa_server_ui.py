from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from igem_drylab.literature.qa import answer_question
from igem_drylab.literature.qa_server import PAGE, health_payload, make_handler


def _evidence_file(tmp_path: Path) -> Path:
    path = tmp_path / "evidence.jsonl"
    path.write_text(json.dumps({"record_id": "oc-1", "title": "OC activity study", "doi": "10.1000/oc", "evidence": "OC activity converts an intermediate in glabridin biosynthesis.", "source_file": "paper.txt", "fields": {"enzyme": "OC", "parameter": "activity"}}) + "\n", encoding="utf-8")
    return path


def test_page_exposes_polished_qa_sections_without_unsafe_source_html() -> None:
    assert "Literature Evidence Explorer" in PAGE
    assert 'id="question-form"' in PAGE
    assert 'id="results"' in PAGE
    assert "checkHealth()" in PAGE
    assert "renderSourceCard" in PAGE
    assert "No matching local evidence found." in PAGE
    assert "Evidence database unavailable." in PAGE
    assert "innerHTML" not in PAGE
    assert "AGENT TOOL" not in PAGE
    assert "Retrieval</b> → Review → Approval" not in PAGE
    assert 'class="help"' in PAGE


def test_health_contract_is_unchanged(tmp_path: Path) -> None:
    evidence = _evidence_file(tmp_path)
    assert health_payload(evidence) == {"ok": True, "evidence_path": str(evidence)}
    assert health_payload(tmp_path / "missing.jsonl")["ok"] is False


def test_local_http_demo_smoke_preserves_root_health_and_qa_routes(tmp_path: Path) -> None:
    evidence = _evidence_file(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(evidence))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/health") as response:
            assert json.loads(response.read())["ok"] is True
        request = Request(base + "/api/qa", data=json.dumps({"question": "OC activity"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request) as response:
            assert json.loads(response.read())["status"] == "retrieved"
        with urlopen(base + "/") as response:
            assert b"Literature Evidence Explorer" in response.read()
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=2)


def test_retrieved_response_keeps_status_answer_and_sources_contract(tmp_path: Path) -> None:
    response = answer_question("What evidence reports OC activity?", _evidence_file(tmp_path))
    assert response["status"] == "retrieved"
    assert isinstance(response["answer"], str)
    source = response["sources"][0]
    assert {"title", "doi", "evidence", "score", "record_id", "source_file", "fields"} <= set(source)


def test_no_match_and_database_unavailable_states_are_backend_compatible(tmp_path: Path) -> None:
    assert answer_question("unrelated-token", _evidence_file(tmp_path))["status"] == "no_match"
    assert answer_question("OC", tmp_path / "missing.jsonl")["status"] == "database_unavailable"
