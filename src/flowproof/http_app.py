from __future__ import annotations

import hmac
import os

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .auth import AuthError, AuthStore, default_store
from .server import app as mcp_app

PUBLIC_PATHS = frozenset({"/health"})
AUTH_PREFIX = "/auth"


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str | None, store: AuthStore, allow_anonymous: bool = False) -> None:
        super().__init__(app)
        self.token = token
        self.store = store
        self.allow_anonymous = allow_anonymous

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith(AUTH_PREFIX):
            return await call_next(request)
        header = request.headers.get("authorization", "")
        presented = header[7:] if header.startswith("Bearer ") else ""
        if self._is_valid(presented):
            return await call_next(request)
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    def _is_valid(self, presented: str) -> bool:
        if not presented:
            return self.allow_anonymous
        if self.token and hmac.compare_digest(presented, self.token):
            return True
        return self.store.user_for_api_key(presented) is not None


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "flowproof",
            "api": "public",
            "mcp": {"endpoint": "/mcp/", "auth": "bearer-key-required"},
            "provenance": "workflow-run-ro-crate",
            "provenanceReceipt": {
                "verifier": "run-linked dataset outputs",
                "checks": [
                    "run action present",
                    "run status present",
                    "hashed outputs present",
                    "hashed outputs linked from the run",
                    "run-linked outputs listed in the dataset",
                    "run output ids are unique",
                    "workflow entity present",
                    "workflow linked from the run",
                ],
            },
            "claimBoundary": "research reproducibility only, not clinical or diagnostic validation",
            "hostedDemoBoundary": "lightweight demo runs only, reference data stays in the user's environment",
            "firstRun": {
                "audience": "research teams connecting an AI client to reproducible pipeline runs",
                "steps": [
                    "create an account",
                    "generate an API key",
                    "add the MCP endpoint to the AI client",
                    "run the assembly-ont pipeline with source data outside the chat transcript",
                    "keep large or sensitive reference data in the local research environment",
                    "review the provenance bundle before sharing results",
                ],
                "proof": "health endpoint exposes auth, MCP, provenance receipt checks, and claim-boundary readiness",
            },
        }
    )


def _store(request: Request) -> AuthStore:
    return request.app.state.auth_store


def _session_user(request: Request) -> int | None:
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        return None
    return _store(request).user_for_session(header[7:])


async def signup(request: Request) -> JSONResponse:
    body = await request.json()
    try:
        user_id = _store(request).create_user(body.get("email", ""), body.get("password", ""))
    except AuthError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    token = _store(request).create_session(user_id)
    return JSONResponse({"session": token}, status_code=201)


async def login(request: Request) -> JSONResponse:
    body = await request.json()
    try:
        user_id = _store(request).authenticate(body.get("email", ""), body.get("password", ""))
    except AuthError as exc:
        return JSONResponse({"error": str(exc)}, status_code=401)
    return JSONResponse({"session": _store(request).create_session(user_id)})


async def create_key(request: Request) -> JSONResponse:
    user_id = _session_user(request)
    if user_id is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    token = _store(request).create_api_key(user_id, body.get("label", "key"))
    return JSONResponse({"key": token}, status_code=201)


async def list_keys(request: Request) -> JSONResponse:
    user_id = _session_user(request)
    if user_id is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    keys = _store(request).list_api_keys(user_id)
    return JSONResponse(
        {"keys": [{"id": k.id, "label": k.label, "prefix": k.prefix, "created_at": k.created_at} for k in keys]}
    )


async def revoke_key(request: Request) -> JSONResponse:
    user_id = _session_user(request)
    if user_id is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    ok = _store(request).revoke_api_key(user_id, int(request.path_params["key_id"]))
    return JSONResponse({"revoked": ok}, status_code=200 if ok else 404)


def build_app(store: AuthStore | None = None) -> Starlette:
    token = os.environ.get("FLOWPROOF_API_TOKEN") or None
    store = store or default_store()
    inner = mcp_app.streamable_http_app()
    inner.state.auth_store = store
    allow_anonymous = os.environ.get("FLOWPROOF_ALLOW_ANONYMOUS", "").lower() in ("1", "true", "yes")
    inner.add_middleware(
        BearerAuthMiddleware, token=token, store=store, allow_anonymous=allow_anonymous
    )
    origins = [o for o in os.environ.get("FLOWPROOF_CORS_ORIGINS", "").split(",") if o]
    if origins:
        inner.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["authorization", "content-type"],
        )
    auth_routes = [
        Route("/health", health, methods=["GET"]),
        Route("/auth/signup", signup, methods=["POST"]),
        Route("/auth/login", login, methods=["POST"]),
        Route("/auth/keys", create_key, methods=["POST"]),
        Route("/auth/keys", list_keys, methods=["GET"]),
        Route("/auth/keys/{key_id:int}", revoke_key, methods=["DELETE"]),
    ]
    for route in reversed(auth_routes):
        inner.router.routes.insert(0, route)
    return inner


asgi = build_app()
