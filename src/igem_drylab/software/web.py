"""Built same-origin frontend and local single-user browser launcher.

The loopback cookie bootstrap is not public multi-user authentication. No
predictor installation, hosted shell or anonymous scientific API is enabled.
"""
from pathlib import Path
import os
import secrets
import socket
import webbrowser
from threading import Thread
from time import sleep

from fastapi import HTTPException
from fastapi.responses import FileResponse


def frontend_location():
    bundled=Path(__file__).parent/'web_static'
    if (bundled/'index.html').is_file(): return bundled
    source=Path(__file__).resolve().parents[3]/'software/dashboard/dist'
    if (source/'index.html').is_file(): return source
    raise RuntimeError('Built browser frontend missing. Install the Web release package, or build it once with pnpm --dir software/dashboard build. Node and Rust are not needed to run a built Web package.')


def mount_frontend(app,root):
    root=Path(root).resolve()
    if not (root/'index.html').is_file(): raise ValueError('built_frontend_index_missing')
    headers={'X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; frame-ancestors 'none'",
        'Referrer-Policy':'same-origin'}
    @app.get('/{web_path:path}',include_in_schema=False)
    def frontend(web_path: str):
        path=(root/web_path).resolve()
        if not path.is_relative_to(root): raise HTTPException(404)
        if path.is_file(): return FileResponse(path,headers=headers)
        if web_path in {'','inputs','workflow','results','tools','settings'}:
            return FileResponse(root/'index.html',headers={**headers,'Cache-Control':'no-store'})
        # Missing API/files/assets must remain 404, not a successful HTML page.
        raise HTTPException(404)


def default_workspace():
    base=Path(os.environ['LOCALAPPDATA']) if os.name=='nt' and os.environ.get('LOCALAPPDATA') else Path.home()/'.local/share'
    return base/'FusionLab/workspace'


def serve_local(*,data_dir=None,port=8780,open_browser=False,frontend_dir=None):
    import uvicorn
    from .dashboard import create_app
    frontend=Path(frontend_dir) if frontend_dir is not None else frontend_location()
    # Reserve and pass the actual socket to Uvicorn: no probe/bind race.
    listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        listener.bind(('127.0.0.1',port))
        listener.listen(128)
    except OSError as error:
        listener.close()
        raise RuntimeError('Cannot open the local port. Stop the other service or choose --port 0 for a free port.') from error
    selected=listener.getsockname()[1]
    origin=f'http://127.0.0.1:{selected}'
    try:
        app=create_app(data_dir=Path(data_dir) if data_dir else default_workspace(),session_token=secrets.token_urlsafe(32),
            frontend_dir=frontend,local_web_origin=origin)
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=selected,log_level='warning'))
        if open_browser:
            def open_when_ready():
                for _ in range(200):
                    if server.should_exit: return
                    if server.started: webbrowser.open(origin); return
                    sleep(.05)
            Thread(target=open_when_ready,daemon=True).start()
        print(f'FusionLab: {origin}\nStop with Ctrl+C. Project data is retained between starts.',flush=True)
        server.run(sockets=[listener])
    finally: listener.close()
