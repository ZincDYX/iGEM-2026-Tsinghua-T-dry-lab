"""Authenticated HTTPS transport only: no local store, engine or tool discovery."""
from contextlib import asynccontextmanager
from pathlib import Path
import ssl

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from starlette.background import BackgroundTask

from .session import configure_session
from .public_contracts import RuntimeInfoView


def remote_url(value: str) -> str:
    url = httpx.URL(value)
    if (url.scheme != "https" or not url.host or url.username or url.password
            or url.query or url.fragment or any(part in {".", ".."} for part in value.split("/"))):
        raise ValueError("Use an HTTPS API base URL without credentials, query or fragment")
    return str(url).rstrip("/")


def create_relay(api_url: str, access_token: str, session_token: str, ca_file: Path | None = None) -> FastAPI:
    base = remote_url(api_url)
    if not access_token or not access_token.isascii() or any(c.isspace() for c in access_token):
        raise ValueError("A nonempty access token without whitespace is required")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)

    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(verify=context, follow_redirects=False, timeout=60,
                                     headers={"Authorization": f"Bearer {access_token}"}) as client:
            try:
                response = await client.get(f"{base}/api/platform/info", timeout=15)
                response.raise_for_status()
                info = RuntimeInfoView.model_validate(response.json())
                if info.name != "FusionLab" or info.authentication != "session_required":
                    raise ValueError("incompatible API")
            except (httpx.HTTPError, ValueError):
                raise RuntimeError("HTTPS API connection failed: check certificate, access token and FusionLab API compatibility") from None
            app.state.upstream = client
            yield

    app = FastAPI(title="FusionLab desktop HTTPS relay", lifespan=lifespan)
    configure_session(app, session_token)

    @app.api_route("/api/platform/{path:path}", methods=["GET", "POST"])
    async def forward(request: Request, path: str):
        # Concatenate the raw API path; never allow an upstream host supplied by a request.
        raw_path = request.scope["raw_path"].decode("ascii")
        url = httpx.URL(base + raw_path, query=request.scope["query_string"] or None)
        if not url.path.startswith(httpx.URL(base).path.rstrip("/") + "/api/platform/"):
            return JSONResponse(status_code=400, content={"detail": {"code": "invalid_api_path"}})
        headers = {key: value for key, value in request.headers.items() if key in {"content-type", "accept", "range"}}
        outgoing = app.state.upstream.build_request(request.method, url, headers=headers, content=request.stream())
        # HTTPX otherwise replays upstream Set-Cookie from its internal jar.
        outgoing.headers.pop("cookie", None)
        try:
            response = await app.state.upstream.send(outgoing, stream=True)
        except httpx.HTTPError:
            # Do not replay POST after a timeout: the upstream may have committed it.
            return JSONResponse(status_code=502, content={"detail": {"code": "remote_connection_failed", "message": "Remote request failed; check its state before repeating a write"}})
        if 300 <= response.status_code < 400:
            await response.aclose()
            return JSONResponse(status_code=502, content={"detail": {"code": "remote_redirect_refused", "message": "Configure the final HTTPS API base URL"}})
        allowed = {"content-type", "content-disposition", "etag", "last-modified", "accept-ranges", "content-range", "cache-control"}
        return StreamingResponse(response.aiter_bytes(), status_code=response.status_code,
                                 headers={k: v for k, v in response.headers.items() if k in allowed},
                                 background=BackgroundTask(response.aclose))

    return app
