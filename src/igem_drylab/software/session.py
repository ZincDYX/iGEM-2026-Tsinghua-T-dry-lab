"""One session-authentication policy for the platform and desktop relay."""
from hmac import compare_digest
from hashlib import sha256
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def configure_session(app: FastAPI, token: str | None, *, local_web_origin: str | None = None) -> None:
    cookie_name='fusionlab_session_'+sha256((local_web_origin or '').encode()).hexdigest()[:12]
    if local_web_origin:
        from starlette.middleware.trustedhost import TrustedHostMiddleware
        parts=urlsplit(local_web_origin)
        if parts.scheme!='http' or parts.hostname not in {'127.0.0.1','localhost','::1'} or not token:
            raise ValueError('local_web_bootstrap_requires_loopback_origin_and_private_token')
        app.add_middleware(TrustedHostMiddleware,allowed_hosts=[parts.hostname])
        @app.post('/api/session/bootstrap')
        def bootstrap(request: Request):
            if (request.client is None or request.client.host not in {'127.0.0.1','::1'}
                or request.headers.get('origin')!=local_web_origin
                or request.headers.get('sec-fetch-site') not in {None,'same-origin'}):
                return JSONResponse(status_code=403,content={'detail':{'code':'local_session_origin_required'}})
            response=JSONResponse({'authentication':'private_http_only_local_session'},headers={'Cache-Control':'no-store'})
            response.set_cookie(cookie_name,token,httponly=True,samesite='strict',path='/api')
            return response
    if token:
        @app.middleware("http")
        async def authenticate(request: Request, call_next):
            if local_web_origin and (request.url.path=='/api/session/bootstrap' or not request.url.path.startswith('/api/')):
                return await call_next(request)
            if request.method != "OPTIONS":
                desktop = request.headers.get("X-FusionLab-Token")
                authorization = request.headers.get("Authorization", "")
                scheme, _, bearer = authorization.partition(" ")
                if authorization and scheme.lower()!='bearer':
                    return JSONResponse(status_code=401,content={'detail':{'code':'unauthorized'}})
                cookie=request.cookies.get(cookie_name,'') if local_web_origin else ''
                supplied = bearer if scheme.lower() == "bearer" else desktop if desktop is not None else cookie
                if cookie and not authorization and desktop is None:
                    origin=request.headers.get('origin')
                    if ((origin is not None and origin!=local_web_origin)
                        or request.headers.get('sec-fetch-site')=='cross-site'
                        or (request.method not in {'GET','HEAD'} and origin!=local_web_origin)):
                        return JSONResponse(status_code=403,content={'detail':{'code':'session_origin_mismatch'}})
                if (desktop is not None and authorization and desktop != supplied) or not compare_digest(supplied.encode(), token.encode()):
                    return JSONResponse(status_code=401, content={"detail": {"code": "unauthorized", "message": "Valid session access token required"}})
            return await call_next(request)
    origins=[local_web_origin] if local_web_origin else ["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"]
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],
        allow_headers=['Content-Type','X-FusionLab-Token','Authorization'])
