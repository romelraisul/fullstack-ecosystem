from fastapi.testclient import TestClient

from backend.app.main import app


def test_orchestrate_quantum_postprocess(mock_quantum_postprocess_fail):
    # Even with post-processing trigger data, endpoint should succeed (structural coverage for deep lines)
    with TestClient(app) as client:
        r = client.post("/orchestrate/quantum", json={"shots": 32})
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("kind") == "bell"
        assert "result" in j
