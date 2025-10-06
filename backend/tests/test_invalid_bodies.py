from fastapi.testclient import TestClient

from backend.app.main import app


def test_orchestrate_delegate_invalid_body():
    with TestClient(app) as client:
        r = client.post(
            "/orchestrate/delegate", json=["not-a-dict"]
        )  # invalid type; code treats as non-dict and defaults
        assert r.status_code in (200, 422)
        if r.status_code == 200:
            j = r.json()
            assert j.get("status") == "ok"


def test_latency_targets_invalid_body():
    with TestClient(app) as client:
        r = client.post("/admin/latency-targets", json=["bad"])
        assert r.status_code in (400, 422)
