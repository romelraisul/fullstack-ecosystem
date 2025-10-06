# Import the backend app
import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure DB path is temp for tests
TEST_DB = Path("test_platform.db")
os.environ["DB_PATH"] = str(TEST_DB)

mod = importlib.import_module("autogen.advanced_backend")
app = mod.app

client = TestClient(app)


def test_workflow_execution_db_failure(monkeypatch):
    """Simulate repository failure during step persistence; ensure 500 not raised to client execution start."""
    # Create workflow first
    wf = {
        "id": "wf1",
        "name": "wf1",
        "description": "demo",
        "steps": [
            {"name": "s1", "agent_id": "agent_a", "parameters": {}, "depends_on": []},
            {"name": "s2", "agent_id": "agent_b", "parameters": {}, "depends_on": ["s1"]},
        ],
        "parallel_execution": False,
        "status": "active",
        "created_at": "2025-01-01T00:00:00",
    }
    mod.workflows["wf1"] = wf

    class DummyRepo:
        def create_execution(self, *a, **k):
            raise RuntimeError("db down")

        def upsert_step_state(self, *a, **k):
            raise RuntimeError("db down")

        def update_execution(self, *a, **k):
            raise RuntimeError("db down")

        def get_execution(self, *a, **k):
            return None

    monkeypatch.setattr(mod, "get_workflows_repo", lambda: DummyRepo())

    resp = client.post("/api/v1/workflows/wf1/execute")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "execution_id" in data


def test_db_queue_overflow(monkeypatch):
    """Fill DB queue beyond threshold and ensure enqueue_db_op returns False without raising."""
    from autogen import advanced_backend as ab

    # Exhaust queue
    for _ in range(ab.DB_MAX_QUEUE_SIZE + 10):
        ab.enqueue_db_op("create_conversation", {"id": "c", "name": "n"})
    # Should be full now
    assert ab.DB_BATCH_QUEUE.qsize() >= ab.DB_MAX_QUEUE_SIZE
    result = ab.enqueue_db_op("add_message", "c", {"id": "m", "role": "user", "content": "hi"})
    assert result is False
