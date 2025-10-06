import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class LargeInventoryClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        # Simulate quick ok for first 5 health endpoints, 404 for others to mix ok/error categories
        if url.endswith("/health"):
            if any(token in url for token in ["sys-0", "sys-1", "sys-2", "sys-3", "sys-4"]):
                return type(
                    "Resp",
                    (),
                    {
                        "status_code": 200,
                        "json": lambda self=None: {"status": "ok"},
                        "raise_for_status": lambda self=None: None,
                    },
                )()
            raise RuntimeError("health fail")
        return type(
            "Resp",
            (),
            {
                "status_code": 404,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
            },
        )()


def test_full_experiment_large_inventory(monkeypatch, set_inventory):
    systems = []
    categories = ["alpha", "beta", "gamma", "delta"]
    for i in range(12):
        systems.append(
            {
                "slug": f"sys-{i}",
                "api_base": f"http://sys-{i}",
                "category": categories[i % len(categories)],
                "maturity": "verified",
            }
        )
    # include qcae minimal to keep quantum section present
    systems.append(
        {"slug": "qcae", "api_base": "http://qcae", "category": "quantum", "maturity": "verified"}
    )
    set_inventory(systems)
    monkeypatch.setattr(httpx, "AsyncClient", LargeInventoryClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 16})
        assert r.status_code == 200
        j = r.json()
        ent = j.get("enterprise_summary", {})
        assert "by_category" in ent
        # Sample array should exist and have at most 5 entries (as per implementation)
        assert "sample" in j
        assert len(j["sample"]) <= 5
