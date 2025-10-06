import builtins
import os

from fastapi.testclient import TestClient

from backend.app.main import app


def test_lifespan_nuanced_failures(monkeypatch, tmp_path):
    original_open = builtins.open

    def selective_open(path, *a, **k):
        # Simulate permission error for first inventory read, then malformed for events registry
        if path.endswith("systems_inventory.json"):
            raise PermissionError("no access")
        if path.endswith("events_registry.json"):
            return original_open(os.path.join(tmp_path, "bad_events.json"), "w", encoding="utf-8")
        return original_open(path, *a, **k)

    # Create malformed events file referenced by our redirected open
    with open(os.path.join(tmp_path, "bad_events.json"), "w", encoding="utf-8") as f:
        f.write("{broken")

    monkeypatch.setattr(builtins, "open", selective_open)
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
