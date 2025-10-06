import builtins

from fastapi.testclient import TestClient

from backend.app.main import app


def test_lifespan_startup_file_read_failures(monkeypatch):
    original_open = builtins.open

    def fake_open(path, *a, **k):  # raise for inventory and events registry
        if path.endswith("systems_inventory.json") or path.endswith("events_registry.json"):
            raise OSError("simulated read failure")
        return original_open(path, *a, **k)

    monkeypatch.setattr(builtins, "open", fake_open)
    # Start client context to trigger lifespan startup; failures should be swallowed
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
