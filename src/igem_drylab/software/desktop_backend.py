"""Local Python process supervised by the thin Tauri desktop shell."""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket

import uvicorn

from .dashboard import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--ready-file", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.pop("FUSIONLAB_SESSION_TOKEN")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    app = create_app(data_dir=args.data_dir, session_token=token)

    @asynccontextmanager
    async def lifespan(_app):
        args.ready_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.ready_file.with_suffix(".tmp")
        temporary.write_text(json.dumps({"url": f"http://127.0.0.1:{port}"}), encoding="utf-8")
        temporary.replace(args.ready_file)
        try:
            yield
        finally:
            args.ready_file.unlink(missing_ok=True)

    app.router.lifespan_context = lifespan
    server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="warning"))
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()


if __name__ == "__main__":
    main()
