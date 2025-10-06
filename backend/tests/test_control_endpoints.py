import os

from fastapi.testclient import TestClient

from backend.app.main import app


def test_control_endpoints_start_stop_restart(monkeypatch):
    called: list[str] = []

    def fake_system(cmd: str):  # capture commands instead of executing
        called.append(cmd)
        return 0

    monkeypatch.setattr(os, "system", fake_system)

    with TestClient(app) as client:
        r1 = client.post("/control/start-all")
        assert r1.status_code == 200
        assert r1.json().get("status") == "ok"

        r2 = client.post("/control/stop-all")
        assert r2.status_code == 200
        assert r2.json().get("status") == "ok"

        r3 = client.post("/control/restart-all")
        assert r3.status_code == 200
        assert r3.json().get("status") == "ok"

    # Ensure the docker-compose commands were attempted in correct order
    assert any("up -d" in c for c in called), called
    assert any("down" in c for c in called), called
    assert any("restart" in c for c in called), called
    # Basic ordering check: start before stop before restart (not strict positional, but occurrence ordering)
    up_idx = next(i for i, c in enumerate(called) if "up -d" in c)
    down_idx = next(i for i, c in enumerate(called) if "down" in c)
    restart_idx = next(i for i, c in enumerate(called) if "restart" in c)
    assert up_idx < down_idx < restart_idx, called
