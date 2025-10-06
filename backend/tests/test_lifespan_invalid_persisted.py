import os

from fastapi.testclient import TestClient

from backend.app.main import LATENCY_TARGETS_FILE, _events_persist_path, app


def test_lifespan_invalid_persisted_files(tmp_path, monkeypatch):
    # Write invalid events_recent file
    events_path = _events_persist_path()
    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    with open(events_path, "w", encoding="utf-8") as f:
        f.write("{not-json")
    # Write invalid latency targets file
    os.makedirs(os.path.dirname(LATENCY_TARGETS_FILE), exist_ok=True)
    with open(LATENCY_TARGETS_FILE, "w", encoding="utf-8") as f:
        f.write("[]}")
    # Startup should swallow errors
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
