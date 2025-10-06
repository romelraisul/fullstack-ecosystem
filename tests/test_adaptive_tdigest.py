import os
import pickle
import time

from fastapi.testclient import TestClient

os.environ["ADAPTIVE_SLO_ENABLED"] = "true"
os.environ["ADAPTIVE_SLO_PERSIST"] = "true"

try:
    from autogen.advanced_backend import _tdigest_store, app, load_tdigests, persist_tdigests
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent / "autogen"))
    from advanced_backend import _tdigest_store, app, load_tdigests, persist_tdigests

client = TestClient(app)


def test_tdigest_persistence_and_quantiles():
    endpoint = "/api/version"
    # Generate latency samples
    for _i in range(1, 21):
        client.get(endpoint)
        time.sleep(0.01)  # Simulate variable latency
    # Persist t-digests
    repo = getattr(app, "workflows_repo", None)
    if repo:
        persist_tdigests(repo, {})
    # Save a copy of the t-digest
    td_before = pickle.dumps(_tdigest_store.get(endpoint))
    # Simulate restart: clear and reload
    _tdigest_store.clear()
    if repo:
        load_tdigests(repo)
    td_after = pickle.dumps(_tdigest_store.get(endpoint))
    assert td_before == td_after, "t-digest should persist and reload identically"
    # Check quantile endpoint
    resp = client.get("/api/v2/latency/quantiles")
    assert resp.status_code == 200
    quantiles = resp.json().get(endpoint)
    assert quantiles is not None
    assert all(k in quantiles for k in ["p50", "p90", "p95", "p99"])
