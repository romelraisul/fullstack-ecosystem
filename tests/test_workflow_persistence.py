from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def test_workflow_create_get_list_roundtrip():
    wf_payload = {
        "name": "wf-persist-check",
        "description": "Workflow persistence test",
        "steps": [
            {"name": "s1", "agent_id": "agent_a", "parameters": {}, "depends_on": []},
            {"name": "s2", "agent_id": "agent_b", "parameters": {}, "depends_on": ["s1"]},
        ],
        "parallel_execution": False,
    }
    create_resp = client.post("/api/v1/workflows", json=wf_payload)
    assert create_resp.status_code == 200, create_resp.text
    wf_id = create_resp.json()["workflow_id"]

    # Fetch single
    get_resp = client.get(f"/api/v1/workflows/{wf_id}")
    assert get_resp.status_code == 200
    single = get_resp.json()
    assert single["id"] == wf_id
    assert len(single["steps"]) == 2

    # List all workflows and verify presence
    list_resp = client.get("/api/v1/workflows")
    assert list_resp.status_code == 200
    data = list_resp.json()
    ids = {w["id"] for w in data["workflows"]}
    assert wf_id in ids
