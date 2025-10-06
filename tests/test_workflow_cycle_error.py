from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def test_workflow_cycle_detection():
    # Create a workflow with a simple 2-step cycle A->B, B->A
    payload = {
        "name": "cycle_wf",
        "description": "Cycle test",
        "steps": [
            {"name": "A", "depends_on": ["B"]},
            {"name": "B", "depends_on": ["A"]},
        ],
    }
    resp = client.post("/api/v1/workflows", json=payload)
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert any("cycle" in (body.get("detail", "") or "").lower() for _ in range(1)), body


def test_workflow_unknown_dependency():
    # Step references a missing dependency
    payload = {
        "name": "unknown_dep_wf",
        "description": "Unknown dep",
        "steps": [
            {"name": "first", "depends_on": ["missing"]},
        ],
    }
    resp = client.post("/api/v1/workflows", json=payload)
    assert resp.status_code == 400, resp.text
    detail = resp.json().get("detail", "").lower()
    assert "unknown step" in detail
