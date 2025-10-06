import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class AllExceptionsClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        raise RuntimeError("network down")


def test_generic_http_all_exceptions(monkeypatch, set_inventory):
    set_inventory(
        [
            {
                "slug": "service-ex",
                "api_base": "http://service-ex",
                "maturity": "verified",
                "category": "alpha",
            }
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", AllExceptionsClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 4})
        assert r.status_code == 200
        j = r.json()
        assert "enterprise_summary" in j
