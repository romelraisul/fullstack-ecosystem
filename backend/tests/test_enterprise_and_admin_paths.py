import builtins
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import _record_event, app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_delegate_enterprise_experiment_internal_failure(monkeypatch, client):
    """Force internal call to /orchestrate/delegate to fail and exercise error branch."""

    class FailingClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None):  # noqa: A002
            # Simulate internal delegate failure
            raise RuntimeError("delegate boom")

    monkeypatch.setattr(httpx, "AsyncClient", FailingClient)
    r = client.post(
        "/orchestrate/delegate-enterprise",
        json={"compute": "experiment", "shots": 32, "dry_run": False},
    )
    # The outer endpoint wraps exceptions into HTTPException 500
    assert r.status_code == 500
    assert "delegate error" in r.json().get("detail", "")


def test_inventory_reload_malformed_json(monkeypatch, tmp_path, client):
    data_dir = Path(os.path.dirname(__file__)).parent.parent / "backend" / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    inv_file = data_dir / "systems_inventory.json"
    inv_file.write_text("{ this is not valid json", encoding="utf-8")
    r = client.post("/admin/reload-inventory")
    assert r.status_code == 500
    assert "Reload failed" in r.json().get("detail", "")


def test_orchestrator_throughput_category_aggregation(client, set_inventory):
    # Prepare inventory with categories
    set_inventory(
        [
            {"slug": "sys-a", "category": "alpha"},
            {"slug": "sys-b", "category": "beta"},
            {"slug": "sys-c", "category": "beta"},
        ]
    )
    # Inject synthetic completion events with mixed categories
    _record_event("system.execute.ok", "sys-a")
    _record_event("system.execute.ok", "sys-b")
    _record_event("system.execute.error", "sys-c")
    r = client.get("/orchestrator/throughput", params={"window_seconds": 60})
    assert r.status_code == 200
    data = r.json()
    assert data["events_count"] >= 3
    by_cat = data.get("by_category", {})
    # Expect alpha:1, beta:2 total events
    assert by_cat.get("alpha") >= 1
    assert by_cat.get("beta") >= 2


def test_persist_events_ring_silent_failure(monkeypatch, client):
    # Monkeypatch open used in _persist_events_ring to raise
    real_open = builtins.open

    def boom_open(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", boom_open)
    # Recording event should not raise despite persistence failure
    _record_event("system.execute.ok", "alpha-mega-system-framework")
    # Restore open for further operations sanity
    monkeypatch.setattr("builtins.open", real_open)
    # Endpoint that triggers persistence indirectly; ensure still works
    r = client.get("/events/recent")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
