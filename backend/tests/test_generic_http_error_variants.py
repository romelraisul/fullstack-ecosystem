import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class StatusOnlyFailClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        # Always return 404 (status path reached, no exception storing last_exc)
        return type(
            "Resp",
            (),
            {
                "status_code": 404,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
            },
        )()


class MixedFailClient(StatusOnlyFailClient):
    async def get(self, url, *a, **k):
        if url.endswith("/health"):
            raise RuntimeError("boom")
        return await super().get(url, *a, **k)


def test_generic_http_status_only_failure(monkeypatch, set_inventory):
    set_inventory(
        [
            {
                "slug": "service-x",
                "api_base": "http://service-x",
                "maturity": "verified",
                "category": "alpha",
            }
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", StatusOnlyFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 4})
        assert r.status_code == 200
        # Structure presence is sufficient
        assert "enterprise_summary" in r.json()


def test_generic_http_mixed_failure(monkeypatch, set_inventory):
    set_inventory(
        [
            {
                "slug": "service-y",
                "api_base": "http://service-y",
                "maturity": "verified",
                "category": "beta",
            }
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", MixedFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 4})
        assert r.status_code == 200
        assert "enterprise_summary" in r.json()
