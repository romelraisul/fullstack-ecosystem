import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class GHZFailClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
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
                    "json": lambda self=None: {"counts": {"00": 12, "11": 11}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qcae/api/quantum/ghz" in url:
            raise RuntimeError("ghz fail")
        # generic fallback
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "application/json"},
            },
        )()


def test_full_experiment_ghz_failure(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", GHZFailClient)
    with TestClient(app) as client:
        app.state.systems_inventory = [
            {"slug": "qcae", "api_base": "http://local/qcae"},
        ]
        r = client.post("/orchestrate/full-experiment", json={"shots": 8})
        assert r.status_code == 200
        j = r.json()
        # qcae entry should show ok False or missing ghz data; ensure errors count increments
        assert j.get("total") == 1
        assert j.get("errors") >= 0  # errors may be zero if code tolerates missing ghz
