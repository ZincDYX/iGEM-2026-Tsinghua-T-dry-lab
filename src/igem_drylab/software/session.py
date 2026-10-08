"""One session-authentication policy for the platform and desktop relay."""
from hmac import compare_digest

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def configure_session(app: FastAPI, token: str | None) -> None:
    if token:
        @app.middleware("http")
        async def authenticate(request: Request, call_next):
            if request.method != "OPTIONS":
                desktop = request.headers.get("X-FusionLab-Token")
                authorization = request.headers.get("Authorization", "")
                scheme, _, bearer = authorization.partition(" ")
                supplied = bearer if scheme.lower() == "bearer" else desktop or ""
                if (desktop is not None and authorization and desktop != supplied) or not compare_digest(supplied.encode(), token.encode()):
                    return JSONResponse(status_code=401, content={"detail": {"code": "unauthorized", "message": "Valid session access token required"}})
            return await call_next(request)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"], allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-FusionLab-Token", "Authorization"])
