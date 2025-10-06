import os
import sys

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def _get_inventory(client: TestClient) -> list[dict]:
    r = client.get("/systems")
    r.raise_for_status()
    data = r.json()
    assert isinstance(data, list)
    return data


def test_systems_summary_and_filter_variants():
    # Exercises /systems/summary gauge updating and /systems/filter query paths.
    with TestClient(app, base_url="http://localhost") as client:
        inv = _get_inventory(client)

        # Summary endpoint
        r_sum = client.get("/systems/summary")
        r_sum.raise_for_status()
        summary = r_sum.json()
        assert "total" in summary and summary["total"] == len(inv)
        assert "by_category" in summary and isinstance(summary["by_category"], dict)
        assert "by_maturity" in summary and isinstance(summary["by_maturity"], dict)

        # If there is at least one experimental system, filter by maturity
        if any(s.get("maturity") == "experimental" for s in inv):
            r = client.get("/systems/filter", params={"maturity": "experimental"})
            r.raise_for_status()
            filtered = r.json()
            assert all(item.get("maturity") == "experimental" for item in filtered)

        # Filter by has_api true
        r_api = client.get("/systems/filter", params={"has_api": "true"})
        r_api.raise_for_status()
        with_api = r_api.json()
        assert all(bool((s.get("api_base") or "").strip()) for s in with_api)

        # Filter by has_api false
        r_no_api = client.get("/systems/filter", params={"has_api": "false"})
        r_no_api.raise_for_status()
        without_api = r_no_api.json()
        assert all(not bool((s.get("api_base") or "").strip()) for s in without_api)


def test_events_recent_ring_and_registry():
    # Hit a few endpoints that generate events then fetch events ring and registry
    with TestClient(app, base_url="http://localhost") as client:
        # Force experimental mutates maturity and emits an event
        client.post("/admin/force-experimental")
        # Fetch inventory summary (no strict asserts beyond status; ensures code path executed)
        client.get("/systems/integration-summary")

        # Events registry
        r_reg = client.get("/events/registry")
        r_reg.raise_for_status()
        reg = r_reg.json()
        assert isinstance(reg, dict)
        assert "events" in reg

        # Recent events (limit param exercise)
        r_recent = client.get("/events/recent", params={"limit": 5})
        r_recent.raise_for_status()
        recent = r_recent.json()
        assert isinstance(recent, list)
        assert 0 < len(recent) <= 5
        # Each event must have required keys
        for evt in recent:
            assert "ts" in evt and "event" in evt and "slug" in evt
