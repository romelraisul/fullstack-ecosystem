import time

from fastapi.testclient import TestClient

from autogen.advanced_backend import app, get_workflows_repo

client = TestClient(app)


class SimulatedDBError(Exception):
    pass


def test_execution_create_db_failure(monkeypatch):
    # Create a workflow definition first
    wf_def = {
        "name": "dbfault1",
        "description": "db fail create",
        "steps": [{"name": "x", "type": "dummy"}],
    }
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200, r.text
    wf_id = r.json()["id"]
    repo = get_workflows_repo()
    if not repo:
        # If repo unavailable, skip since test only meaningful with persistence layer
        return
    # Monkeypatch create_execution to raise
    monkeypatch.setattr(
        repo,
        "create_execution",
        lambda *a, **k: (_ for _ in ()).throw(SimulatedDBError("boom create")),
    )
    r2 = client.post(f"/api/v1/workflows/{wf_id}/execute")
    # Should still succeed (fall back to in-memory) returning execution id
    assert r2.status_code == 200
    exec_id = r2.json()["execution_id"]
    assert exec_id


def test_step_persistence_failure(monkeypatch):
    wf_def = {
        "name": "dbfault2",
        "description": "db fail step",
        "steps": [
            {"name": "s1", "type": "dummy"},
            {"name": "s2", "type": "dummy", "depends_on": ["s1"]},
        ],
    }
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200
    wf_id = r.json()["id"]
    repo = get_workflows_repo()
    if not repo:
        return
    # Patch upsert_step_state to raise after first invocation
    call_count = {"n": 0}
    orig = repo.upsert_step_state

    def failing_upsert(*a, **k):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise SimulatedDBError("boom step")
        return orig(*a, **k)

    monkeypatch.setattr(repo, "upsert_step_state", failing_upsert)
    r2 = client.post(f"/api/v1/workflows/{wf_id}/execute")
    assert r2.status_code == 200
    exec_id = r2.json()["execution_id"]
    # Poll for completion
    deadline = time.time() + 8
    while time.time() < deadline:
        g = client.get(f"/api/v1/workflows/executions/{exec_id}")
        if g.status_code == 200 and g.json().get("execution", {}).get("status") in (
            "success",
            "failed",
        ):
            break
        time.sleep(0.3)
    assert g.status_code == 200
    # Even with one step persistence failure workflow should have proceeded
    assert g.json()["execution"]["steps_completed"] >= 1


def test_replay_db_get_failure(monkeypatch):
    wf_def = {
        "name": "dbfault3",
        "description": "db fail replay",
        "steps": [{"name": "a", "type": "dummy"}],
    }
    r = client.post("/api/v1/workflows", json=wf_def)
    assert r.status_code == 200
    wf_id = r.json()["id"]
    r2 = client.post(f"/api/v1/workflows/{wf_id}/execute")
    assert r2.status_code == 200
    exec_id = r2.json()["execution_id"]
    # Wait completion
    deadline = time.time() + 6
    while time.time() < deadline:
        g = client.get(f"/api/v1/workflows/executions/{exec_id}")
        if g.status_code == 200 and g.json().get("execution", {}).get("status") in (
            "success",
            "failed",
        ):
            break
        time.sleep(0.25)
    repo = get_workflows_repo()
    if not repo:
        return
    monkeypatch.setattr(
        repo, "get_execution", lambda *a, **k: (_ for _ in ()).throw(SimulatedDBError("boom get"))
    )
    # Replay should fall back to in-memory record or return 404 if not present
    rep = client.post(f"/api/v1/workflows/executions/{exec_id}/replay")
    assert rep.status_code in (200, 404)
