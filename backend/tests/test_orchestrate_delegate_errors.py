import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class MixedAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        if url.endswith("/system/sys-b/execute"):
            raise RuntimeError("boom")
        return type("Resp", (), {"status_code": 200, "json": lambda self=None: {"ok": True}})()


def test_delegate_mixed_success_and_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", MixedAsyncClient)
    with TestClient(app) as client:
        # Set inventory after startup so it's not overwritten
        app.state.systems_inventory = [
            {"slug": "sys-a", "api_base": "http://local/a"},
            {"slug": "sys-b", "api_base": "http://local/b"},
        ]
        r = client.post(
            "/orchestrate/delegate",
            json={"event": "unit.test", "dry_run": False, "targets": ["sys-a", "sys-b"]},
        )
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        # Confirm we targeted exactly the two systems
        assert j.get("total") == 2
        # Expect at least one error due to raised exception for sys-b
        assert j.get("errors") >= 1
        assert j.get("ok") <= 1
        assert isinstance(j.get("sample"), list)
