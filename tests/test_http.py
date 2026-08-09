from __future__ import annotations

import pytest

pytest.importorskip("starlette")
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from flowproof.auth import AuthStore
from flowproof.http_app import BearerAuthMiddleware, health


def _app(token: str | None, store: AuthStore | None = None, allow_anonymous: bool = False) -> Starlette:
    async def protected(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    store = store or AuthStore(":memory:")
    app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/mcp/", protected, methods=["POST"]),
        ]
    )
    app.add_middleware(
        BearerAuthMiddleware, token=token, store=store, allow_anonymous=allow_anonymous
    )
    return app


def test_health_is_public_even_with_token():
    with TestClient(_app("secret")) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["service"] == "flowproof"


def test_protected_route_rejects_missing_token():
    with TestClient(_app("secret")) as client:
        assert client.post("/mcp/").status_code == 401


def test_protected_route_rejects_wrong_token():
    with TestClient(_app("secret")) as client:
        r = client.post("/mcp/", headers={"authorization": "Bearer nope"})
        assert r.status_code == 401


def test_protected_route_accepts_correct_token():
    with TestClient(_app("secret")) as client:
        r = client.post("/mcp/", headers={"authorization": "Bearer secret"})
        assert r.status_code == 200


def test_fails_closed_when_no_token_configured():
    with TestClient(_app(None)) as client:
        assert client.post("/mcp/").status_code == 401


def test_anonymous_only_when_explicitly_enabled():
    with TestClient(_app(None, allow_anonymous=True)) as client:
        assert client.post("/mcp/").status_code == 200


def test_valid_per_user_key_grants_access(tmp_path):
    store = AuthStore(tmp_path / "auth.db")
    uid = store.create_user("sci@lab.org", "supersecret")
    key = store.create_api_key(uid, "laptop")
    with TestClient(_app("admin-token", store)) as client:
        assert client.post("/mcp/", headers={"authorization": f"Bearer {key}"}).status_code == 200


def test_revoked_key_denied(tmp_path):
    store = AuthStore(tmp_path / "auth.db")
    uid = store.create_user("sci@lab.org", "supersecret")
    key = store.create_api_key(uid, "laptop")
    store.revoke_api_key(uid, store.list_api_keys(uid)[0].id)
    with TestClient(_app("admin-token", store)) as client:
        assert client.post("/mcp/", headers={"authorization": f"Bearer {key}"}).status_code == 401


def test_real_app_exposes_health(monkeypatch):
    monkeypatch.setenv("FLOWPROOF_API_TOKEN", "secret")
    from flowproof.http_app import build_app

    with TestClient(build_app()) as client:
        assert client.get("/health").status_code == 200
