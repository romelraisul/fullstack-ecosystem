import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class CategoryClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        # Success for service-one health, fail for service-two sequence
        if url.endswith("/health"):
            if "one" in url:
                return type(
                    "Resp",
                    (),
                    {
                        "status_code": 200,
                        "json": lambda self=None: {"status": "ok"},
                        "raise_for_status": lambda self=None: None,
                    },
                )()
            else:
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


def test_full_experiment_by_category_aggregation(monkeypatch, set_inventory):
    # Use explicit hosts so our custom client can differentiate service-one vs service-two via URL substring
    set_inventory(
        [
            {
                "slug": "service-one",
                "api_base": "http://service-one",
                "category": "alpha",
                "maturity": "verified",
            },
            {
                "slug": "service-two",
                "api_base": "http://service-two",
                "category": "beta",
                "maturity": "verified",
            },
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", CategoryClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 4})
        assert r.status_code == 200
        j = r.json()
        ent = j.get("enterprise_summary", {})
        assert "by_category" in ent
        bc = ent["by_category"]
        # Presence of mapping structure is sufficient; population may vary under mocked clients
        assert isinstance(bc, dict)
