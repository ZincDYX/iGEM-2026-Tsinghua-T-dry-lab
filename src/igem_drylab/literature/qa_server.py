"""Local-only browser page for the offline evidence retriever.

This intentionally exposes no upload, arbitrary command, or API-key endpoint.
Start it with a fixed evidence path and visit the printed localhost URL.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .qa import answer_question

PAGE = """<!doctype html><meta charset=utf-8><title>iGEM evidence QA</title>
<main><h1>Local literature evidence QA</h1><p>Searches only the server's fixed local evidence database. Verify each quoted source before use.</p>
<form id=q><input id=question required placeholder='Ask about a parameter or result'><button>Search</button></form><pre id=result></pre></main>
<script>q.onsubmit=async e=>{e.preventDefault();let r=await fetch('/api/qa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:question.value})});result.textContent=JSON.stringify(await r.json(),null,2)}</script>"""


def serve(evidence_path: Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve a fixed evidence file. Bind localhost by default for safety."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path == "/health":
                self._json({"ok": evidence_path.is_file(), "evidence_path": str(evidence_path)})
            elif urlparse(self.path).path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers(); self.wfile.write(body)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/qa":
                self.send_error(HTTPStatus.NOT_FOUND); return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 20_000:
                    raise ValueError("request body is too large")
                payload = json.loads(self.rfile.read(length))
                question = payload.get("question") if isinstance(payload, dict) else None
                if not isinstance(question, str) or not question.strip():
                    raise ValueError("question must be a non-empty string")
                self._json(answer_question(question, evidence_path))
            except (ValueError, json.JSONDecodeError) as exc:
                self._json({"ok": False, "status": "invalid_request", "answer": str(exc), "sources": []}, HTTPStatus.BAD_REQUEST)

        def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Evidence QA listening at http://{host}:{port}/ (database: {evidence_path})")
    server.serve_forever()
