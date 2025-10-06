import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class GenericFailClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        # Return success for qcae health and bell to isolate generic failure
        if "/qcae/health" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"status": "ok"},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qcae/api/quantum/bell" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": {"00": 5, "11": 5}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qcae/api/quantum/ghz" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": {"000": 3, "111": 2}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        # Generic systems always error
        raise RuntimeError("generic fail")


def test_full_experiment_generic_http_failures(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", GenericFailClient)
    with TestClient(app) as client:
        app.state.systems_inventory = [
            {"slug": "qcae", "api_base": "http://local/qcae"},
            {"slug": "alpha", "api_base": "http://local/alpha"},
            {"slug": "beta", "api_base": "http://local/beta"},
        ]
        r = client.post("/orchestrate/full-experiment", json={"shots": 8})
        assert r.status_code == 200
        j = r.json()
        assert j.get("total") == 3
        # Expect errors for 2 generic systems
        assert j.get("errors") >= 2
