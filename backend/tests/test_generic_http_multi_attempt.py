import types

import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class MultiAttemptClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *args, **kwargs):
        # First call 404, second call 200; subsequent 200
        self.calls.append(url)
        if len(self.calls) == 1:
            return types.SimpleNamespace(
                status_code=404,
                json=lambda: {},
                raise_for_status=lambda: None,
                headers={"content-type": "application/json"},
            )
        return types.SimpleNamespace(
            status_code=200,
            json=lambda: {"ok": True},
            raise_for_status=lambda: None,
            headers={"content-type": "application/json"},
        )


def test_generic_http_multi_attempt(monkeypatch, set_inventory):
    # Inventory with one non-quantum system and api_base so generic path executes
    set_inventory(
        [
            {
                "slug": "alpha-mega-system-framework",
                "maturity": "verified",
                "api_base": "/api",
                "category": "core",
            },
            {
                "slug": "other-service",
                "maturity": "verified",
                "api_base": "/other",
                "category": "core",
            },
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", MultiAttemptClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 8})
        assert r.status_code == 200
        j = r.json()
        assert "enterprise_summary" in j
        # Either both ok or one ok depending on attempt logic; ensure sample present
        assert "sample" in j
