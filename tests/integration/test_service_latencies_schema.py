import time

import pytest
import requests

API_BASE = "http://localhost:8010"


@pytest.mark.integration
def test_service_latencies_schema_basic():
    url = f"{API_BASE}/api/service-latencies?limit=5"
    # Retry loop in case sampler hasn't populated yet
    deadline = time.time() + 10
    data = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data.get("services"):
                    break
        except Exception:  # pragma: no cover - network flake
            pass
        time.sleep(0.5)
    assert isinstance(data, dict), f"Response not JSON object: {data}"
    assert "updatedAt" in data, "Missing updatedAt"
    services = data.get("services")
    assert isinstance(services, list) and services, "services list empty"
    svc = services[0]
    for key in ["name", "url", "samples", "stats"]:
        assert key in svc, f"Missing key {key} in service entry"
    stats = svc["stats"]
    expected_stat_keys = {
        "attempts",
        "ok",
        "failure_rate_pct",
        "latest_ms",
        "min_ms",
        "max_ms",
        "p50_ms",
        "p90_ms",
        "p99_ms",
        "latest_class",
        "count",
    }
    assert expected_stat_keys.issubset(stats.keys()), f"Stats keys mismatch: {stats.keys()}"
    # Failure rate should be within 0-100 if present
    fr = stats.get("failure_rate_pct")
    if fr is not None:
        assert 0 <= fr <= 100, f"failure_rate_pct out of range: {fr}"
    # latest_class should be one of enumerated values
    assert stats.get("latest_class") in {"good", "warn", "high", "na"}
