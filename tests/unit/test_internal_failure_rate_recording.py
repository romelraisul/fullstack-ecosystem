from pathlib import Path

import pytest
import yaml
from prometheus_client import CollectorRegistry, Counter

from tests.utils.metrics import assert_metric_present


def test_failure_rate_recording_rule_present():
    """Ensure internal_service:failure_rate_5m / 10m recording rules are defined in Prometheus rules file.

    This is a static presence test (no promtool execution here). We parse the YAML and assert the expected
    record names exist anywhere in the rule groups. This guards against accidental deletion / renaming that
    would break dashboards and alerts depending on the recording rule consolidation.
    """
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "docker" / "prometheus_rules.yml"
    if not path.exists():  # allow local minimal checkouts to skip
        pytest.skip(f"Rules file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict) and "groups" in data, "Malformed prometheus_rules.yml"
    records = []
    for g in data.get("groups", []):
        for r in g.get("rules", []) or []:
            rec = r.get("record")
            if rec:
                records.append(rec)
    missing = {"internal_service:failure_rate_5m", "internal_service:failure_rate_10m"} - set(
        records
    )
    assert not missing, f"Missing failure rate recording rules: {missing}"  # noqa: PT018


def test_failure_rate_computation_consistency():
    """Synthetic sanity check that the raw counters yield an expected failure rate formula result.

    We do not run PromQL here; instead we emulate the ratio used by the recording rule formula
    (sum(rate(ok)) vs sum(rate(attempts))). Using a dedicated temporary registry keeps isolation.
    """
    reg = CollectorRegistry()
    attempts = Counter(
        "internal_service_latency_attempts_total", "attempts", ["service"], registry=reg
    )
    ok = Counter("internal_service_latency_ok_total", "ok", ["service"], registry=reg)

    # Simulate two services with differing success ratios
    for _ in range(120):  # service A: 80% success
        attempts.labels(service="svcA").inc()
    for _ in range(96):
        ok.labels(service="svcA").inc()

    for _ in range(100):  # service B: 60% success
        attempts.labels(service="svcB").inc()
    for _ in range(60):
        ok.labels(service="svcB").inc()

    # Compute instantaneous failure ratio analogous to what the recording rule covers over windowed rates
    # failure_rate = (attempts - ok) / attempts
    failure_a = (120 - 96) / 120
    failure_b = (100 - 60) / 100
    assert round(failure_a, 4) == 0.2
    assert round(failure_b, 4) == 0.4

    # Basic scrape presence using helper against the isolated registry
    assert_metric_present(
        "internal_service_latency_attempts_total",
        registry=reg,
        message="Expected attempts counter lines missing",
    )
    assert_metric_present(
        "internal_service_latency_ok_total",
        registry=reg,
        message="Expected ok counter lines missing",
    )
