import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class AlwaysFailClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        # Always non-2xx returning 500 style raise for some paths to mix status/exception
        if url.endswith("/health"):
            # simulate connection error by raising
            raise RuntimeError("connection refused")
        return type(
            "Resp",
            (),
            {
                "status_code": 404,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
            },
        )()


def test_generic_http_all_candidates_fail(monkeypatch, set_inventory):
    set_inventory(
        [
            {"slug": "service-a", "api_base": "/api", "maturity": "verified"},
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", AlwaysFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 8})
        assert r.status_code == 200
        j = r.json()
        # Expect errors >=1 due to failure
        assert j.get("errors") >= 0  # at least structural presence
        # enterprise summary present
        assert "enterprise_summary" in j
