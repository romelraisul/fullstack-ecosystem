from fastapi.testclient import TestClient

from governance_app.app import app
from governance_app.persistence import DB_PATH, init_db, record_run

client = TestClient(app)


def setup_function(_):
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def test_stats_aggregation():
    # Seed: repo A two runs (3 findings), repo B one run (2 findings)
    record_run(
        repo="org/A",
        branch="main",
        workflows_scanned=1,
        findings=[
            {
                "workflow": "a.yml",
                "issues": [
                    {"action": "actions/checkout", "ref": "v4", "pinned": True, "internal": False},
                    {"action": "someorg/act1", "ref": "v1", "pinned": False, "internal": False},
                ],
            }
        ],
    )
    record_run(
        repo="org/A",
        branch="dev",
        workflows_scanned=1,
        findings=[
            {
                "workflow": "a.yml",
                "issues": [
                    {"action": "someorg/act1", "ref": "v1", "pinned": False, "internal": False}
                ],
            }
        ],
    )
    record_run(
        repo="org/B",
        branch="main",
        workflows_scanned=1,
        findings=[
            {
                "workflow": "b.yml",
                "issues": [
                    {"action": "actions/checkout", "ref": "v4", "pinned": True, "internal": False},
                    {"action": "anotherorg/act2", "ref": "v2", "pinned": False, "internal": False},
                ],
            }
        ],
    )

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_runs"] == 3
    assert data["total_findings"] == 5

    repos = {r["repo"]: r for r in data["repos"]}
    assert repos["org/A"]["runs"] == 2
    assert repos["org/A"]["findings"] == 3
    assert repos["org/B"]["runs"] == 1
    assert repos["org/B"]["findings"] == 2

    actions = {a["action"]: a for a in data["actions"]}
    assert actions["actions/checkout"]["occurrences"] == 2
    assert actions["actions/checkout"]["pinned"] == 2
    assert actions["someorg/act1"]["occurrences"] == 2
    assert actions["someorg/act1"]["unpinned"] == 2
    assert actions["anotherorg/act2"]["occurrences"] == 1
