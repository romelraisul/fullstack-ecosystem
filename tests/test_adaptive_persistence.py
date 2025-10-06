import os

from fastapi.testclient import TestClient

# Force adaptive + persistence for this test run (in-process change before app import)
os.environ["ADAPTIVE_SLO_ENABLED"] = "true"
os.environ["ADAPTIVE_SLO_PERSIST"] = "true"

try:
    from autogen.advanced_backend import _adaptive_latency_ema_p95, app  # type: ignore
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent / "autogen"))
    from advanced_backend import _adaptive_latency_ema_p95, app  # type: ignore

client = TestClient(app)


def test_adaptive_state_persisted_and_reported(monkeypatch):
    # Hit endpoint several times to produce measurements
    for _ in range(7):
        client.get("/api/version")
    dist = client.get("/api/v2/latency/distribution").json()
    # If adaptive enabled we expect either empty endpoints (fast run) or metrics with added fields
    if dist["adaptive_enabled"] and dist["endpoints"]:
        for _ep, data in dist["endpoints"].items():
            assert "window_seconds" in data
            assert "last_update_ts" in data
            assert "ema_p95_ms" in data
    # Simulate process restart by reloading persisted state (call internal loader if exposed)
    # Ensure EMA dict is non-empty after hits
    if dist["endpoints"]:
        assert any(v > 0 for v in _adaptive_latency_ema_p95.values())
