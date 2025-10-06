import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class QuantumBellAndGHZFailClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        # health ok, bell & ghz fail
        if url.endswith("/health"):
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"status": "ok"},
                    "raise_for_status": lambda self=None: None,
                },
            )()
        if "/api/quantum/bell" in url or "/api/quantum/ghz" in url:
            raise RuntimeError("quantum failure")
        return type(
            "Resp",
            (),
            {
                "status_code": 404,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
            },
        )()


def test_full_experiment_combined_quantum_fail(monkeypatch, set_inventory):
    set_inventory(
        [
            {"slug": "qcae", "api_base": "http://qcae", "maturity": "verified"},
            {"slug": "alpha-mega-system-framework", "api_base": "/api", "maturity": "verified"},
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", QuantumBellAndGHZFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 32})
        assert r.status_code == 200
        j = r.json()
        # Ensure response structure present even when both quantum sub-steps failed
        assert "quantum" in j
        assert "enterprise_summary" in j
