import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class DummyEnterpriseDelegateClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        # simulate delegate endpoint response structure expected when ok
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: {
                    "status": "ok",
                    "total": len(json.get("payload", {})),
                    "ok": 0,
                    "errors": 0,
                    "duration_ms": 1.23,
                },
            },
        )()


def _inject_inventory():
    app.state.systems_inventory = [
        {"slug": "sys-a", "api_base": "http://local/a", "category": "cat1", "maturity": "stable"},
        {
            "slug": "sys-b",
            "api_base": "http://local/b",
            "category": "cat2",
            "maturity": "experimental",
        },
    ]


def test_delegate_enterprise_light_dry_run(monkeypatch):
    _inject_inventory()
    monkeypatch.setattr(httpx, "AsyncClient", DummyEnterpriseDelegateClient)
    with TestClient(app) as client:
        r = client.post(
            "/orchestrate/delegate-enterprise", json={"dry_run": True, "compute": "light"}
        )
        assert r.status_code == 200
        j = r.json()
        # Combined view should include enterprise summary keys
        assert j.get("status") == "ok"
        assert j.get("compute_mode") == "light"
        assert "enterprise" in j
        assert j.get("enterprise", {}).get("source") == "light"
        assert j.get("event") == "enterprise.summary.delegated"


def test_delegate_enterprise_experiment_dry_run(monkeypatch):
    _inject_inventory()

    # For experiment mode, patch AsyncClient to also handle full-experiment call path gracefully
    class DummyClientExp(DummyEnterpriseDelegateClient):
        async def post(self, url, json=None, headers=None):
            if url.endswith("/orchestrate/full-experiment"):
                # simulate full-experiment return containing enterprise_summary
                return type(
                    "Resp",
                    (),
                    {
                        "status_code": 200,
                        "json": lambda self=None: {
                            "enterprise_summary": {"inventory": {}},
                            "total": 1,
                            "ok": 1,
                            "errors": 0,
                            "duration_ms": 5,
                        },
                    },
                )()
            return await super().post(url, json=json, headers=headers)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClientExp)
    with TestClient(app) as client:
        r = client.post(
            "/orchestrate/delegate-enterprise",
            json={"dry_run": True, "compute": "experiment", "shots": 8},
        )
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("compute_mode") == "experiment"
        assert j.get("event") == "enterprise.summary.delegated"
        ent = j.get("enterprise")
        assert ent.get("source") == "experiment"
