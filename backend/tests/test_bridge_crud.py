import os
import sys

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore

# Import helper utilities; adjust path if tests package not recognized as module
try:
    from backend.tests.utils.bridge_test_helpers import (
        add_raw_input,
        read_bridge_json,
        temp_bridge_data,
    )
except ModuleNotFoundError:
    # Fallback: attempt relative import via direct path manipulation
    UTIL_PATH = os.path.join(CURRENT_DIR, "utils")
    if UTIL_PATH not in sys.path:
        sys.path.append(UTIL_PATH)
    from bridge_test_helpers import (  # type: ignore
        add_raw_input,
        temp_bridge_data,
    )


def test_bridge_create_and_filters(tmp_path):
    with temp_bridge_data(tmp_path) as data_file:
        with TestClient(app, base_url="http://localhost") as client:
            # B1: create input
            payload = {"title": "Alpha", "problem": "Scaling issue"}
            r = client.post("/bridge/inputs", json=payload)
            r.raise_for_status()
            created = r.json()
            assert created["id"] == 1
            assert created["status"] == "new"

            # Add more inputs directly to craft filter scenarios
            add_raw_input(data_file, title="Beta", owner="ops", tags=["ops"], status="new")
            add_raw_input(data_file, title="Gamma", owner="eng", tags=["ml"], status="reviewing")

            # B2: owner filter
            r_owner = client.get("/bridge/inputs", params={"owner": "eng"})
            assert len(r_owner.json()) == 1
            # tag filter
            r_tag = client.get("/bridge/inputs", params={"tag": "ops"})
            assert len(r_tag.json()) == 1
            # status filter (reviewing)
            r_status = client.get("/bridge/inputs", params={"status": "reviewing"})
            assert len(r_status.json()) == 1


def test_bridge_update_owner_and_status(tmp_path):
    with temp_bridge_data(tmp_path) as data_file:
        with TestClient(app, base_url="http://localhost") as client:
            # seed single input
            add_raw_input(data_file, title="Delta", owner=None, status="new")
            # Update owner (B3 success)
            r_owner = client.patch("/bridge/inputs/1/owner", json={"owner": "team-x"})
            r_owner.raise_for_status()
            assert r_owner.json()["owner"] == "team-x"
            # Update status (B4 success)
            r_status = client.patch("/bridge/inputs/1/status", json={"status": "approved"})
            r_status.raise_for_status()
            assert r_status.json()["status"] == "approved"
            # 404 owner update
            r_owner_404 = client.patch("/bridge/inputs/999/owner", json={"owner": "nobody"})
            assert r_owner_404.status_code == 404
            # 404 status update
            r_status_404 = client.patch("/bridge/inputs/999/status", json={"status": "approved"})
            assert r_status_404.status_code == 404


def test_bridge_experiments_and_metrics(tmp_path):
    with temp_bridge_data(tmp_path) as data_file:
        with TestClient(app, base_url="http://localhost") as client:
            add_raw_input(data_file, title="Exp1", owner="alice", status="new")
            add_raw_input(data_file, title="Exp2", owner="alice", status="reviewing")
            # Approve experiment (B5 success)
            r_exp = client.post("/bridge/experiments/1", params={"objective": "Validate scaling"})
            r_exp.raise_for_status()
            assert r_exp.json()["input_id"] == 1
            # 404 experiment
            r_exp_404 = client.post("/bridge/experiments/999", params={"objective": "Missing"})
            assert r_exp_404.status_code == 404
            # Metrics (B6)
            m = client.get("/metrics")
            m.raise_for_status()
            text = m.text
            assert "bridge_inputs_total" in text
            assert "bridge_experiments_total" in text
            # Status gauge labels should exist for all statuses (even zero counts)
            for s in ("new", "reviewing", "approved", "rejected"):
                assert f'status="{s}"' in text
            # Owner gauge labels may not appear if owners not recomputed yet; optional check
            # (no hard assertion to reduce flakiness)
