import os
import time

from fastapi.testclient import TestClient

from governance_app.app import _stats_cache, app
from governance_app.persistence import DB_PATH, init_db, record_run

client = TestClient(app)


def setup_function(_):
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    # Reset cache
    _stats_cache["data"] = None
    _stats_cache["expires"] = 0.0
    os.environ["STATS_CACHE_TTL_SECONDS"] = "60"


def test_stats_cache_returns_cached_data():
    # Seed initial run
    record_run(
        repo="org/repo",
        branch="main",
        workflows_scanned=1,
        findings=[{"workflow": "a.yml", "issues": []}],
    )
    first = client.get("/stats").json()
    assert first["total_runs"] == 1

    # Add another run AFTER first fetch (would make total_runs=2 if cache not used)
    record_run(
        repo="org/repo",
        branch="main",
        workflows_scanned=1,
        findings=[{"workflow": "b.yml", "issues": []}],
    )
    cached = client.get("/stats").json()
    assert cached["total_runs"] == 1, "Should still be cached"

    # Force expiry by manipulating cache expiry to past
    _stats_cache["expires"] = time.time() - 1
    refreshed = client.get("/stats").json()
    assert refreshed["total_runs"] == 2, "Should reflect new run after expiry"
