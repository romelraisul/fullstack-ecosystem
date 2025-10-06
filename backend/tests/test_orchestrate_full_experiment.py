import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class FullExperimentClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        # Identify which subsystem based on URL
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
                    "json": lambda self=None: {"counts": {"00": 10, "11": 9}},
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
                    "json": lambda self=None: {"counts": {"000": 5, "111": 4}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qdc/health" in url:
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
        if "/qdc/api/deployment-metrics" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {
                        "total_qubits_deployed": 42,
                        "operational_systems": 7,
                        "active_contracts": 3,
                    },
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qcms/health" in url:
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
        if "/qcms/api/consciousness-status" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {
                        "merger_completion_rate": 0.95,
                        "intelligence_nodes_active": 12,
                    },
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/qcc/health" in url:
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
        # Generic attempts -> simulate first candidate success
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


def test_full_experiment_minimal(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FullExperimentClient)
    with TestClient(app) as client:
        app.state.systems_inventory = [
            {
                "slug": "qcae",
                "api_base": "http://local/qcae",
                "category": "quantum",
                "maturity": "stable",
            },
            {
                "slug": "qdc",
                "api_base": "http://local/qdc",
                "category": "quantum",
                "maturity": "stable",
            },
            {
                "slug": "qcms",
                "api_base": "http://local/qcms",
                "category": "cog",
                "maturity": "stable",
            },
            {
                "slug": "qcc",
                "api_base": "http://local/qcc",
                "category": "control",
                "maturity": "stable",
            },
            {
                "slug": "alpha-mega-system-framework",
                "api_base": "http://local/alpha",
                "category": "meta",
                "maturity": "stable",
            },
        ]
        r = client.post("/orchestrate/full-experiment", json={"shots": 16})
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("total") == 5
        assert j.get("ok") == 5
        assert isinstance(j.get("quantum", {}).get("bell_top"), list)
        assert isinstance(j.get("quantum", {}).get("ghz_top"), list)
        assert isinstance(j.get("enterprise_summary"), dict)
