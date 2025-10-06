import time

from fastapi.testclient import TestClient

from autogen.advanced_backend import app, workflows

client = TestClient(app)


def _wait_for_execution(execution_id: str, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/v1/workflows/executions/{execution_id}")
        if r.status_code == 200:
            data = r.json()
            status = data.get("execution", {}).get("status")
            if status in ("success", "failed"):
                return data
        time.sleep(0.2)
    raise AssertionError(f"Execution {execution_id} did not complete in time")


def test_workflow_replay_persists_lineage_and_snapshot():
    # create a simple workflow
    wf_def = {
        "name": "replay_demo",
        "description": "Test replay lineage",
        "steps": [
            {"name": "s1", "type": "dummy"},
            {"name": "s2", "type": "dummy", "depends_on": ["s1"]},
        ],
    }
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200, r.text
    wf_id = r.json()["id"]
    assert wf_id in workflows

    # start execution
    r = client.post(f"/api/v1/workflows/{wf_id}/execute")
    assert r.status_code == 200, r.text
    exec_id = r.json()["execution_id"]

    data = _wait_for_execution(exec_id)
    assert data["execution"]["status"] == "success"
    # verify snapshot present
    snapshot = data["execution"].get("input_snapshot")
    assert snapshot and snapshot.get("workflow_id") == wf_id
    assert len(snapshot.get("steps", [])) == 2

    # replay
    r = client.post(f"/api/v1/workflows/executions/{exec_id}/replay")
    assert r.status_code == 200, r.text
    replay_exec_id = r.json()["execution_id"]
    assert r.json()["replay_of"] == exec_id

    replay_data = _wait_for_execution(replay_exec_id)
    assert replay_data["execution"]["status"] == "success"
    assert replay_data["execution"].get("replay_of") == exec_id
    rsnapshot = replay_data["execution"].get("input_snapshot")
    assert rsnapshot and rsnapshot.get("workflow_id") == wf_id
    assert len(rsnapshot.get("steps", [])) == 2
