import time


def test_conversation_create_and_add_message(client, auth_headers):
    # Create conversation
    r = client.post(
        "/api/v1/conversations",
        json={
            "name": "Test Conv",
            "description": "",
            "agent_id": "nonexistent-agent",  # triggers fallback generic response
            "user_message": "Hello system",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    conv_id = r.json()["conversation_id"]

    # Add message
    r2 = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Next msg"},
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    assert "response" in r2.json()

    # List
    r3 = client.get("/api/v1/conversations", headers=auth_headers)
    assert r3.status_code == 200
    convs = r3.json()["conversations"]
    assert any(c["id"] == conv_id for c in convs)


def test_workflow_execution_basic(client, auth_headers):
    # Create simple two-step linear workflow
    wf = {
        "name": "wf1",
        "description": "test wf",
        "steps": [
            {"name": "step1", "agent_id": "a1", "parameters": {}, "depends_on": []},
            {"name": "step2", "agent_id": "a2", "parameters": {}, "depends_on": ["step1"]},
        ],
        "parallel_execution": False,
    }
    r = client.post("/api/v1/workflows", json=wf, headers=auth_headers)
    assert r.status_code == 200, r.text
    wf_id = r.json()["workflow_id"]

    exec_r = client.post(f"/api/v1/workflows/{wf_id}/execute", headers=auth_headers)
    assert exec_r.status_code == 200, exec_r.text
    execution_id = exec_r.json()["execution_id"]

    # Poll for completion (bounded attempts)
    for _ in range(15):
        status_r = client.get(f"/api/v1/workflows/executions/{execution_id}", headers=auth_headers)
        assert status_r.status_code == 200
        data = status_r.json()["execution"]
        if data["status"] in ("success", "failed"):
            break
        time.sleep(0.2)
    assert data["status"] == "success"
