from datetime import datetime

from fastapi.testclient import TestClient

from autogen.advanced_backend import app, get_workflows_repo

client = TestClient(app)


def test_perf_history_empty():
    r = client.get("/api/v2/perf/history?days=7")
    assert r.status_code == 200
    data = r.json()
    assert data["days"] == 7
    assert isinstance(data.get("items"), list)


def test_upsert_daily_perf_and_fetch():
    repo = get_workflows_repo()
    if not repo or not hasattr(repo, "upsert_daily_perf"):
        return
    today = datetime.utcnow().date().isoformat()
    repo.upsert_daily_perf(today, "GET /api/v1/ping", 42.0, 90.0, 100)
    repo.upsert_daily_perf(today, "POST /api/v1/workflows/{id}/execute", 120.0, None, 15)
    r = client.get("/api/v2/perf/history?days=1")
    assert r.status_code == 200
    data = r.json()
    items = data["items"]
    assert any(i["endpoint"] == "GET /api/v1/ping" and i["median_ms"] == 42.0 for i in items)
