import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class DummyResponse:
    def __init__(self, status_code=200, json_body=None):
        self.status_code = status_code
        self._json_body = json_body or {"status": "ok", "echo": True}

    def json(self):
        return self._json_body


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        # simulate a quick success response
        return DummyResponse(
            200,
            {
                "status": "ok",
                "url": url,
                "event": json.get("event") if isinstance(json, dict) else None,
            },
        )


def test_orchestrate_demo_and_delegate(monkeypatch):
    # Inject a minimal systems inventory with api_base so demo picks them up
    app.state.systems_inventory = [
        {"slug": "alpha-mega-system-framework", "api_base": "http://local/a"},
        {"slug": "adjacent-markets-command-center", "api_base": "http://local/b"},
        {"slug": "ipo-acceleration-command", "api_base": "http://local/c"},
    ]

    # Monkeypatch AsyncClient to avoid real HTTP calls
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    with TestClient(app) as client:
        # Demo orchestrate
        r_demo = client.post("/orchestrate/demo", json={})
        assert r_demo.status_code == 200
        jd = r_demo.json()
        assert jd.get("status") == "ok"
        assert isinstance(jd.get("planned"), list)
        # Implementation may yield fewer than 3 if filtering changes; just ensure consistency
        assert len(jd.get("executed")) == len(jd.get("planned"))

        # Delegate orchestrate (dry_run true to skip internal loop)
        r_delegate = client.post(
            "/orchestrate/delegate", json={"dry_run": True, "event": "unit.test"}
        )
        assert r_delegate.status_code == 200
        jdel = r_delegate.json()
        assert jdel.get("status") == "ok"
        assert jdel.get("dry_run") is True
        assert isinstance(jdel.get("planned"), list)
        assert jdel.get("executed") == []
