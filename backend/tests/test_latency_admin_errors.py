import os
import sys

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def test_latency_targets_error_cases():
    with TestClient(app, base_url="http://localhost") as client:
        # L1: non-dict body triggers FastAPI validation (422) before handler executes
        r1 = client.post("/admin/latency-targets", json=[])
        assert r1.status_code == 422
        # L2: missing targets key
        r2 = client.post("/admin/latency-targets", json={})
        assert r2.status_code == 400
        # L3: empty targets list
        r3 = client.post("/admin/latency-targets", json={"targets": []})
        assert r3.status_code == 400
        # L4: invalid entries (blank fields)
        r4 = client.post("/admin/latency-targets", json={"targets": [{"name": "", "url": ""}]})
        assert r4.status_code == 400
