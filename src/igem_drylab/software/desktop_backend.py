"""Local Python process supervised by the thin Tauri desktop shell."""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket

import uvicorn

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.pop("FUSIONLAB_SESSION_TOKEN")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    api_url = os.environ.pop("FUSIONLAB_HTTPS_API_URL", "")
    if api_url:
        from .https_relay import create_relay
        app = create_relay(api_url, os.environ.pop("FUSIONLAB_HTTPS_ACCESS_TOKEN"), token,
                           Path(value) if (value := os.environ.pop("FUSIONLAB_HTTPS_CA_FILE", "")) else None)
    else:
        from .dashboard import create_app
        app = create_app(data_dir=args.data_dir, session_token=token)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(_app):
        # Startup IPC belongs to the parent pipe, not the user's filesystem.
        # In particular, encrypted/redirected Windows profiles may reject rename.
        async with original_lifespan(_app):
            print(json.dumps({"url": f"http://127.0.0.1:{port}"}), flush=True)
            yield

    app.router.lifespan_context = lifespan
    server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="warning"))
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()


if __name__ == "__main__":
    main()
