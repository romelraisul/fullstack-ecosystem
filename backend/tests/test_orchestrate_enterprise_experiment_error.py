import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class ExperimentErrorClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        # Simulate internal full-experiment failing
        if url.endswith("/orchestrate/full-experiment"):
            raise RuntimeError("full-exp boom")
        # Delegate attempt returns ok minimal structure
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: {
                    "status": "ok",
                    "total": 0,
                    "ok": 0,
                    "errors": 0,
                    "duration_ms": 0,
                    "sample": [],
                },
            },
        )()


def test_delegate_enterprise_experiment_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", ExperimentErrorClient)
    with TestClient(app) as client:
        app.state.systems_inventory = []
        r = client.post(
            "/orchestrate/delegate-enterprise",
            json={"dry_run": False, "compute": "experiment", "shots": 4},
        )
        # Even with experiment internal failure, we still expect 200 from delegate call combining error payload
        assert r.status_code == 200
        j = r.json()
        ent = j.get("enterprise")
        # Source experiment but includes error field
        assert ent.get("source") == "experiment"
        assert "error" in ent or "note" in ent
