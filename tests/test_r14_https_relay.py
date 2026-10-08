"""Actual local TLS sockets and explicit protocol fixtures; no scientific solver."""
from datetime import datetime, timedelta, timezone
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import ssl
from threading import Thread

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
import pytest

from igem_drylab.software.https_relay import create_relay, remote_url
from igem_drylab.software.dashboard import create_app

TOKEN = "SOFTWARE_TLS_FIXTURE_ACCESS_NOT_REAL"
LOCAL = "SOFTWARE_LOOPBACK_FIXTURE_NOT_REAL"
INFO = dict(name="FusionLab", protocol_version="2", authentication="session_required",
            workspace_id="SOFTWARE_TLS_FIXTURE", storage="SQLite WAL", max_workers=1,
            plugin_sandbox=False, agent_backend="validated_workflow_templates", capabilities={},
            resources={}, remote_desktop_authenticated_session=True, supported_rate_laws=[])


@pytest.fixture
def tls_api(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False).sign(key, hashes.SHA256()))
    ca, private = tmp_path / "fixture-ca.pem", tmp_path / "fixture-key.pem"
    ca.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    calls = []
    info = dict(INFO)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.handle_api()

        def do_POST(self):
            self.handle_api()

        def handle_api(self):
            if self.headers.get("Transfer-Encoding") == "chunked":
                body = bytearray()
                while (size := int(self.rfile.readline().strip(), 16)):
                    body.extend(self.rfile.read(size))
                    self.rfile.read(2)
                self.rfile.readline()
                body = bytes(body)
            else:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            calls.append(dict(path=self.path, headers=dict(self.headers), body=body))
            status, data, headers = 200, body, {}
            if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                status, data = 401, b'{"detail":{"code":"unauthorized"}}'
            elif self.path == "/api/platform/info":
                data = json.dumps(info).encode()
                headers["Content-Type"] = "application/json"
            elif self.path == "/api/platform/redirect":
                status = 307
                headers["Location"] = "https://another.invalid/leak"
            elif self.path == "/api/platform/compressed":
                data = gzip.compress(b"EXACT_ORIGINAL_DOWNLOAD_BYTES")
                headers["Content-Encoding"] = "gzip"
                headers["Content-Disposition"] = 'attachment; filename="source.txt"'
            elif self.path == "/api/platform/denied":
                status, data = 403, b'{"detail":{"code":"fixture_denied"}}'
            headers["Set-Cookie"] = "upstream-private-cookie=not-forwarded"
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ca, private)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://localhost:{server.server_port}", ca, calls, info
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("value", ["http://example.invalid", "https://user:pass@example.invalid", "https://example.invalid?token=x", "https://example.invalid#x", "https://example.invalid/../outside"])
def test_remote_requires_private_explicit_https_base(value):
    with pytest.raises(ValueError):
        remote_url(value)


def test_verified_tls_auth_headers_raw_binary_query_and_response(tls_api):
    url, ca, calls, _ = tls_api
    app = create_relay(url, TOKEN, LOCAL, ca)
    with TestClient(app, headers={"X-FusionLab-Token": LOCAL}) as api:
        assert api.get("/api/platform/info").json() == INFO
        payload = b"\x00\xffSOFTWARE_BINARY\n" * 9000
        result = api.post("/api/platform/echo?name=a%2Bb", content=payload, headers={"Content-Type": "application/octet-stream", "Cookie": "local-private=x"})
        assert result.content == payload
        assert calls[-1]["path"] == "/api/platform/echo?name=a%2Bb"
        assert calls[-1]["body"] == payload
        assert calls[-1]["headers"]["Authorization"] == f"Bearer {TOKEN}"
        assert "X-FusionLab-Token" not in calls[-1]["headers"] and "Cookie" not in calls[-1]["headers"]
        assert "set-cookie" not in result.headers
        before = len(calls)
        assert api.get("/api/platform/info", headers={"X-FusionLab-Token": "wrong"}).status_code == 401
        assert len(calls) == before
        assert api.get("/api/dashboard/dag").status_code == 404
        assert api.get("/api/platform/denied").status_code == 403
        assert api.get("/api/platform/redirect").status_code == 502
        assert not any("another.invalid" in call["path"] for call in calls)
        download = api.get("/api/platform/compressed")
        assert download.content == b"EXACT_ORIGINAL_DOWNLOAD_BYTES"
        assert download.headers["content-disposition"].endswith('"source.txt"')
        assert "content-encoding" not in download.headers
    assert not hasattr(app.state, "platform_store") and not hasattr(app.state, "workflow_engine")


@pytest.mark.parametrize("fault", ["untrusted_certificate", "wrong_hostname", "wrong_token", "incompatible_protocol", "anonymous_service"])
def test_startup_refuses_unverified_or_incompatible_api(tls_api, fault):
    url, ca, _, info = tls_api
    if fault == "incompatible_protocol":
        info["protocol_version"] = "unexpected"
    if fault == "anonymous_service":
        info["authentication"] = "anonymous"
    if fault == "wrong_hostname":
        url = url.replace("localhost", "127.0.0.1")
    app = create_relay(url, "wrong" if fault == "wrong_token" else TOKEN, LOCAL, None if fault == "untrusted_certificate" else ca)
    with pytest.raises(RuntimeError, match="check certificate, access token") as error:
        with TestClient(app):
            pass
    assert TOKEN not in str(error.value) and url not in str(error.value)


def test_remote_error_does_not_retry_committed_write(tls_api):
    url, ca, calls, _ = tls_api
    app = create_relay(url, TOKEN, LOCAL, ca)
    with TestClient(app, headers={"X-FusionLab-Token": LOCAL}) as api:
        class CommittedThenTimeout:
            writes = 0
            def build_request(self, *args, **kwargs):
                import httpx
                return httpx.Request("POST", "https://example.invalid/api/platform/projects")
            async def send(self, *args, **kwargs):
                self.writes += 1
                import httpx
                raise httpx.ReadTimeout("SOFTWARE_TIMEOUT_AFTER_COMMIT")
        transport = CommittedThenTimeout()
        app.state.upstream = transport
        assert api.post("/api/platform/projects", json={}).status_code == 502
        assert transport.writes == 1
    # This one timeout is explicitly a transport stub, not claimed real network failure.


def test_platform_accepts_bearer_without_disabling_desktop_auth(tmp_path):
    app = create_app(data_dir=tmp_path, session_token=TOKEN, discover_tools=False)
    with TestClient(app) as api:
        assert api.get("/api/platform/info", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
        assert api.get("/api/platform/info", headers={"X-FusionLab-Token": TOKEN}).status_code == 200
        assert api.get("/api/platform/info", headers={"Authorization": f"Bearer {TOKEN}", "X-FusionLab-Token": "conflicting"}).status_code == 401
        assert api.get("/api/platform/info", headers={"Authorization": b"Bearer \xff"}).status_code == 401
