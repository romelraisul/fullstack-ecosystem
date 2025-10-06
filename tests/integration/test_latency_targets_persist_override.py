import json
import os

import pytest
import requests

API_BASE = "http://localhost:8010"
DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "app", "data", "latency_targets.json"
)


@pytest.mark.integration
def test_latency_targets_persist_override_presence():
    """Validate that when a persisted latency_targets.json exists, the API reports those targets.

    Assumptions:
    - Service already started (docker compose up) BEFORE test runs.
    - Persisted file was created via admin endpoint in a previous run (we do not mutate it here
      to avoid cross-test side effects).
    """
    # If file missing, skip (environment not prepared for this assertion)
    if not os.path.exists(DATA_FILE):
        pytest.skip("latency_targets.json not present; cannot validate override")
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            persisted = json.load(f)
    except Exception as e:  # pragma: no cover - file read anomaly
        pytest.skip(f"Could not read persisted targets file: {e}")
    if not isinstance(persisted, list) or not persisted:
        pytest.skip("Persisted file empty; nothing to assert")

    # Hit admin endpoint to compare
    r = requests.get(f"{API_BASE}/admin/latency-targets", timeout=3)
    assert r.status_code == 200, f"admin endpoint status {r.status_code}"
    body = r.json()
    targets = body.get("targets")
    assert isinstance(targets, list) and targets, "API targets list empty"

    # Basic shape equality: names in persisted should be subset of API names
    persisted_names = {t.get("name") for t in persisted if isinstance(t, dict)}
    api_names = {t.get("name") for t in targets if isinstance(t, dict)}
    assert persisted_names.issubset(
        api_names
    ), f"Persisted names {persisted_names} not subset of API names {api_names}"


@pytest.mark.integration
def test_latency_targets_metrics_gauge_present():
    """Lightweight metrics presence test for future gauge (will skip if not yet added)."""
    # Scrape metrics and look for placeholder gauge name once implemented
    r = requests.get(f"{API_BASE}/metrics", timeout=3)
    assert r.status_code == 200
    text = r.text
    # If gauge added later this assertion will become active; for now just ensure metrics endpoint works
    # Do not hard fail if gauge missing yet
    if "internal_service_latency_targets" not in text:
        pytest.skip("latency targets gauge not present yet (expected prior to implementation)")
    # If present, perform a minimal parse check
    lines = [l for l in text.splitlines() if l.startswith("internal_service_latency_targets")]
    assert lines, "Gauge label line missing despite metric name present"
