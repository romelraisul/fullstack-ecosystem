from fastapi.testclient import TestClient

from governance_app.app import app
from governance_app.persistence import DB_PATH, init_db, record_run


def setup_function(_):
    # fresh db per test
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def seed_runs(n=5):
    for i in range(n):
        record_run(
            repo=f"org/repo{i % 2}",
            branch="main",
            workflows_scanned=1,
            findings=[
                {
                    "workflow": f"wf{i}.yml",
                    "issues": [
                        {
                            "action": "actions/checkout",
                            "ref": "v4",
                            "pinned": True,
                            "internal": False,
                        },
                        {
                            "action": f"someorg/act{i}",
                            "ref": "v1",
                            "pinned": False,
                            "internal": False,
                        },
                    ],
                }
            ],
        )


client = TestClient(app)


def test_runs_pagination_limit_offset():
    seed_runs(6)
    r1 = client.get("/runs", params={"limit": 2, "offset": 0})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["limit"] == 2
    assert len(body1["items"]) == 2

    r2 = client.get("/runs", params={"limit": 2, "offset": 2})
    body2 = r2.json()
    ids_page1 = {item["id"] for item in body1["items"]}
    ids_page2 = {item["id"] for item in body2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


def test_findings_filter_run():
    seed_runs(1)
    # Grab run id
    runs_resp = client.get("/runs", params={"limit": 1})
    run_id = runs_resp.json()["items"][0]["id"]
    findings_resp = client.get("/findings", params={"run_id": run_id, "limit": 10})
    assert findings_resp.status_code == 200
    body = findings_resp.json()
    assert body["run_id"] == run_id
    assert body["count"] == len(body["items"])
    # expect two findings inserted per seed run
    assert body["count"] == 2


def test_findings_pagination():
    seed_runs(2)  # 4 findings total
    runs_resp = client.get("/runs", params={"limit": 1})
    run_id = runs_resp.json()["items"][0]["id"]
    all_findings = client.get("/findings", params={"run_id": run_id, "limit": 100}).json()["items"]
    page1 = client.get("/findings", params={"run_id": run_id, "limit": 1, "offset": 0}).json()[
        "items"
    ]
    page2 = client.get("/findings", params={"run_id": run_id, "limit": 1, "offset": 1}).json()[
        "items"
    ]
    assert page1[0]["id"] != page2[0]["id"]
    assert len(all_findings) >= 2


def test_runs_findings_subresource():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    record_run(
        repo="org/repo",
        branch="main",
        workflows_scanned=1,
        findings=[
            {
                "workflow": "wf.yml",
                "issues": [
                    {"action": "actions/checkout", "ref": "v4", "pinned": True, "internal": False},
                    {"action": "someorg/act", "ref": "v1", "pinned": False, "internal": False},
                ],
            }
        ],
    )
    client = TestClient(app)
    runs_resp = client.get("/runs", params={"limit": 1})
    rid = runs_resp.json()["items"][0]["id"]
    sub_resp = client.get(f"/runs/{rid}/findings", params={"limit": 10})
    assert sub_resp.status_code == 200
    body = sub_resp.json()
    assert body["run_id"] == rid
    assert body["total"] == 2
    assert len(body["items"]) == 2
