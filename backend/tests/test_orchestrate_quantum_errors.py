import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class QuantumHealthFailClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        raise RuntimeError("health unreachable")


class QuantumBellFailClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
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
        if "/api/quantum/bell" in url:
            raise RuntimeError("bell failed")
        return type(
            "Resp",
            (),
            {
                "status_code": 500,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: (_ for _ in ()).throw(Exception("bad")),
            },
        )()


def test_quantum_health_failure(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumHealthFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/quantum", json={"shots": 64})
        assert r.status_code == 503


def test_quantum_bell_failure(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumBellFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/quantum", json={"shots": 64})
        assert r.status_code == 500
