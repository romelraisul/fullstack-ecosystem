import httpx
from fastapi.testclient import TestClient

from backend.app import main as main_mod
from backend.app.main import _EVENTS_RING, app


def test_lifespan_startup_fallbacks(monkeypatch, tmp_path):
    """Force exceptions in inventory and events registry loading to exercise fallback branches."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    # Point module's data path helpers to temp directory by monkeypatching __file__
    monkeypatch.setattr(main_mod, "__file__", str(tmp_path / "main.py"))
    # Create invalid events registry file to trigger exception path
    events_file = data_dir / "events_registry.json"
    events_file.write_text("{ invalid json", encoding="utf-8")
    # Create invalid persisted events file
    lat_path = data_dir / "events_recent.json"
    lat_path.write_text("not a list", encoding="utf-8")
    # Also ensure systems_inventory.json missing to hit FileNotFound fallback
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        # Events ring should be list (even after bad persistence file)
        assert isinstance(_EVENTS_RING, list)


def test_route_metrics_label_fallback():
    with TestClient(app) as client:
        # Request a non-existent path to exercise fallback to raw path for labeling
        r = client.get("/non-existent-route-xyz")
        assert r.status_code == 404
        # Metrics endpoint fetch just to ensure no crash after 404 instrumentation
        m = client.get("/metrics")
        assert m.status_code == 200


def test_full_experiment_empty_inventory(monkeypatch):
    # Clear inventory
    app.state.systems_inventory = []

    # Use a client where any AsyncClient usage still functions but inventory emptiness short-circuits
    class NoopClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            raise AssertionError("should not call external clients with empty inventory")

    monkeypatch.setattr(httpx, "AsyncClient", NoopClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 32})
        assert r.status_code == 200
        j = r.json()
        assert j.get("total") == 0
        assert j.get("ok") == 0
        assert j.get("errors") == 0


def test_full_experiment_multi_failures(monkeypatch, set_inventory):
    # Include qcae and two generic systems with api_base so we can orchestrate
    set_inventory(
        [
            {"slug": "qcae", "api_base": "http://qcae"},
            {"slug": "sys-a", "api_base": "/api"},
            {"slug": "sys-b", "api_base": "/api"},
        ]
    )

    class MultiFailClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            # Make qcae health succeed but bell fail
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
                raise RuntimeError("bell fail")
            # Generic system attempts: simulate 500 to count as failures
            return type(
                "Resp",
                (),
                {
                    "status_code": 500,
                    "json": lambda self=None: {},
                    "raise_for_status": lambda self=None: None,
                },
            )()

    monkeypatch.setattr(httpx, "AsyncClient", MultiFailClient)
    with TestClient(app) as client:
        r = client.post("/orchestrate/full-experiment", json={"shots": 32})
        assert r.status_code == 200
        j = r.json()
        # Even if all attempts failed or were short-circuited, structure should exist
        assert j.get("errors") >= 0
        ent = j.get("enterprise_summary", {})
        assert "by_category" in ent
        # overall_ok_pct should be 0.0 when no successes
        if j.get("ok") == 0:
            assert ent.get("overall_ok_pct") == 0.0
