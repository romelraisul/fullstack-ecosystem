import json
import os
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def _temp_inventory_path() -> Path:
    data_dir = Path(os.path.dirname(__file__)).parent / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "systems_inventory.json"


def test_reload_inventory_success_and_error(tmp_path):
    # Backup real file if exists
    inv_path = _temp_inventory_path()
    backup = None
    if inv_path.exists():
        backup = inv_path.read_text(encoding="utf-8")

    try:
        # Write a valid inventory file
        systems = [
            {"slug": "svc-a", "maturity": "verified", "api_base": "http://a"},
            {"slug": "svc-b", "maturity": "experimental", "api_base": ""},
        ]
        inv_path.write_text(json.dumps(systems), encoding="utf-8")
        with TestClient(app, base_url="http://localhost") as client:
            r_ok = client.post("/admin/reload-inventory")
            r_ok.raise_for_status()
            data = r_ok.json()
            assert data.get("status") == "ok"
            assert data.get("total") == 2
            assert "last_reload_at" in data

        # Corrupt file to trigger error
        inv_path.write_text('{"not": "a list"}', encoding="utf-8")
        with TestClient(app, base_url="http://localhost") as client:
            r_fail = client.post("/admin/reload-inventory")
            assert r_fail.status_code == 500
            body = r_fail.json()
            assert "Reload failed" in body.get("detail", "")
    finally:
        # Restore
        if backup is not None:
            inv_path.write_text(backup, encoding="utf-8")


def test_enterprise_achievements_structure():
    with TestClient(app, base_url="http://localhost") as client:
        r = client.get("/enterprise/achievements")
        r.raise_for_status()
        data = r.json()
        assert "achievements" in data and isinstance(data["achievements"], list)
        assert any("Enterprise Readiness" in ach.get("title", "") for ach in data["achievements"])


def test_latency_targets_and_service_latencies_aggregation(monkeypatch):
    # Inject fake latency targets and synthetic samples to exercise aggregation code
    with TestClient(app, base_url="http://localhost") as client:
        # Set targets (no persistence) so latency history structures exist
        body = {
            "targets": [
                {"name": "api", "url": "http://api/health"},
                {"name": "gateway", "url": "http://gateway/health"},
            ],
            "persist": False,
        }
        r_set = client.post("/admin/latency-targets", json=body)
        r_set.raise_for_status()

        # Manually inject samples into app.state.latency_history
        history = app.state.latency_history
        now = time.time()
        samples_api = [
            {"ts": now - 3, "ms": 100.0, "status": 200, "ok": True, "cls": "good"},
            {"ts": now - 2, "ms": 160.0, "status": 200, "ok": True, "cls": "warn"},
            {"ts": now - 1, "ms": 500.0, "status": 500, "ok": False, "cls": "na"},
        ]
        samples_gw = [
            {"ts": now - 2, "ms": 50.0, "status": 200, "ok": True, "cls": "good"},
            {"ts": now - 1, "ms": 75.0, "status": 200, "ok": True, "cls": "good"},
        ]
        history["api"].extend(samples_api)
        history["gateway"].extend(samples_gw)

        r_lat = client.get("/api/service-latencies", params={"limit": 10})
        r_lat.raise_for_status()
        payload = r_lat.json()
        services = payload.get("services", [])
        assert len(services) == 2
        api_entry = next(s for s in services if s["name"] == "api")
        gw_entry = next(s for s in services if s["name"] == "gateway")
        # api stats: only ok samples count for ms stats; attempts may include background sampler cycle
        assert api_entry["stats"]["attempts"] >= 3
        assert api_entry["stats"]["ok"] >= 2
        assert api_entry["stats"]["latest_class"] in (
            "na",
            "warn",
            "good",
        )  # depending on ordering logic
        assert gw_entry["stats"]["count"] >= 2


def test_orchestrator_heartbeat_event_emission(monkeypatch):
    # We can't easily speed the background task without modifying code, so we directly call the internal recorder
    from app.main import _record_event  # type: ignore

    with TestClient(app, base_url="http://localhost") as client:
        _record_event("orchestrator.heartbeat", "orchestrator")
        r_recent = client.get("/events/recent", params={"limit": 20})
        r_recent.raise_for_status()
        items = r_recent.json()
        assert any(evt.get("event") == "orchestrator.heartbeat" for evt in items)
