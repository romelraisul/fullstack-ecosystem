import json
import os
import time
import urllib.error
import urllib.request

import pytest

PROM_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
RULE_TARGETS = [
    "internal_service:failure_rate_5m",
    "internal_service:failure_rate_10m",
    "internal_service:p99_latency_seconds_5m",
    "internal_service:p99_latency_seconds_30m",
]


def _query(expr: str):
    url = f"{PROM_URL}/api/v1/query?query={urllib.parse.quote(expr)}"
    with urllib.request.urlopen(url, timeout=3) as r:  # nosec B310
        data = json.loads(r.read().decode("utf-8"))
    return data


@pytest.mark.integration
def test_recording_rules_materialize():
    """Smoke check that key recording rule time series materialize in a live Prometheus.

    Skips if Prometheus is unreachable. Retries for up to ~30s to allow initial evaluation cycles.
    """
    if os.environ.get("SKIP_LIVE_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_LIVE_TESTS set; skipping live Prometheus recording rules test")
    # Reachability check
    try:
        _ = _query("up")
    except Exception:
        pytest.skip("Prometheus not reachable on PROMETHEUS_URL")

    missing = set(RULE_TARGETS)
    deadline = time.time() + 30
    attempt = 0
    while missing and time.time() < deadline:
        attempt += 1
        still_missing = set()
        for metric in list(missing):
            try:
                data = _query(metric)
                if data.get("status") == "success":
                    result = data.get("data", {}).get("result", [])
                    if result:  # at least one series present
                        missing.discard(metric)
                    else:
                        still_missing.add(metric)
                else:
                    still_missing.add(metric)
            except (urllib.error.URLError, TimeoutError):
                still_missing.add(metric)
            except Exception:
                still_missing.add(metric)
        if still_missing:
            time.sleep(3)
    if missing:
        pytest.fail(f"Recording rule metrics missing after wait: {sorted(missing)}")
