import os
import sys
import time

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def test_latency_sampler_failure_injected():
    with TestClient(app, base_url="http://localhost") as client:
        # Ensure at least one target exists (reuse existing or set minimal)
        if not getattr(app.state, "latency_targets", []):
            client.post(
                "/admin/latency-targets",
                json={"targets": [{"name": "api", "url": "http://api/health"}], "persist": False},
            )
        targets = app.state.latency_targets
        name = targets[0]["name"]
        history = app.state.latency_history
        dq = history.get(name)
        assert dq is not None
        # Append failing sample
        dq.append({"ts": time.time(), "ms": 1000.0, "status": 500, "ok": False, "cls": "na"})
        r = client.get("/api/service-latencies", params={"limit": 5})
        r.raise_for_status()
        payload = r.json()
        svc = next(s for s in payload["services"] if s["name"] == name)
        assert svc["stats"]["attempts"] >= 1
        # failure_rate_pct should be not None when attempts exist
        assert svc["stats"]["failure_rate_pct"] is not None
