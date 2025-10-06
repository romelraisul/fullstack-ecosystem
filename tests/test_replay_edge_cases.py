import time

from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def _wait(exec_id):
    deadline = time.time() + 8
    while time.time() < deadline:
        r = client.get(f"/api/v1/workflows/executions/{exec_id}")
        if r.status_code == 200 and r.json().get("execution", {}).get("status") in (
            "success",
            "failed",
        ):
            return r.json()
        time.sleep(0.25)
    raise AssertionError("Execution did not finish")


def test_replay_missing_execution():
    r = client.post("/api/v1/workflows/executions/not-real/replay")
    assert r.status_code == 404


def test_replay_in_progress_conflict():
    wf_def = {"name": "replay_inprog", "description": "", "steps": [{"name": "a", "type": "dummy"}]}
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200
    wf_id = r.json()["id"]
    r2 = client.post(f"/api/v1/workflows/{wf_id}/execute")
    assert r2.status_code == 200
    exec_id = r2.json()["execution_id"]
    # Immediately attempt replay before completion
    rep = client.post(f"/api/v1/workflows/executions/{exec_id}/replay")
    assert rep.status_code == 409
    # Let it finish then replay ok
    _wait(exec_id)
    rep2 = client.post(f"/api/v1/workflows/executions/{exec_id}/replay")
    assert rep2.status_code == 200


def test_multi_generation_lineage():
    wf_def = {"name": "replay_chain", "description": "", "steps": [{"name": "s", "type": "dummy"}]}
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200
    wf_id = r.json()["id"]
    # First execution
    r1 = client.post(f"/api/v1/workflows/{wf_id}/execute")
    e1 = r1.json()["execution_id"]
    _wait(e1)
    # Replay -> e2
    r2 = client.post(f"/api/v1/workflows/executions/{e1}/replay")
    assert r2.status_code == 200
    e2 = r2.json()["execution_id"]
    _wait(e2)
    # Replay e2 -> e3
    r3 = client.post(f"/api/v1/workflows/executions/{e2}/replay")
    assert r3.status_code == 200
    e3 = r3.json()["execution_id"]
    _wait(e3)
    # Validate lineage chain e3->e2->e1
    j3 = client.get(f"/api/v1/workflows/executions/{e3}").json()
    j2 = client.get(f"/api/v1/workflows/executions/{e2}").json()
    assert j3["execution"]["replay_of"] == e2
    assert j2["execution"]["replay_of"] == e1
