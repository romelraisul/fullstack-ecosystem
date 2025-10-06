import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class SimpleAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        return type("Resp", (), {"status_code": 200, "json": lambda self=None: {"ok": True}})()


def test_delegate_excludes_experimental(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", SimpleAsyncClient)
    with TestClient(app) as client:
        app.state.systems_inventory = [
            {"slug": "stable-a", "api_base": "http://local/a", "maturity": "stable"},
            {"slug": "exp-b", "api_base": "http://local/b", "maturity": "experimental"},
        ]
        r = client.post(
            "/orchestrate/delegate",
            json={"include_experimental": False, "dry_run": True, "targets": ["stable-a", "exp-b"]},
        )
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        planned = j.get("planned")
        assert planned == ["stable-a"]
