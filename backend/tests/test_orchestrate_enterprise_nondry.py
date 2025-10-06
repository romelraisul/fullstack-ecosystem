import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class DelegateClientNonDry:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        # Simulate successful delegate invocation returning aggregated stats
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: {
                    "status": "ok",
                    "total": 2,
                    "ok": 2,
                    "errors": 0,
                    "duration_ms": 2.5,
                    "sample": [{"slug": "sys-a", "ok": True}],
                },
            },
        )()


def test_delegate_enterprise_nondry(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DelegateClientNonDry)
    with TestClient(app) as client:
        # Provide minimal inventory for enterprise summary computation
        app.state.systems_inventory = [
            {
                "slug": "sys-a",
                "api_base": "http://local/a",
                "category": "cat1",
                "maturity": "stable",
            },
            {
                "slug": "sys-b",
                "api_base": "http://local/b",
                "category": "cat1",
                "maturity": "experimental",
            },
        ]
        r = client.post(
            "/orchestrate/delegate-enterprise", json={"dry_run": False, "compute": "light"}
        )
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("event") == "enterprise.summary.delegated"
        assert j.get("compute_mode") == "light"
        assert isinstance(j.get("enterprise"), dict)
        assert j.get("total") == 2
