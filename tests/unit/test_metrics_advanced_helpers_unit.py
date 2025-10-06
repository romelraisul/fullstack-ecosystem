from __future__ import annotations

import math

from prometheus_client import CollectorRegistry, Counter, Histogram

from tests.utils.metrics import (
    approximate_histogram_quantiles,
    assert_counter_monotonic,
    registry_snapshot,
)


def test_registry_snapshot_and_monotonic_violation() -> None:
    before = CollectorRegistry()
    after = CollectorRegistry()
    Counter("events_total", "events", ["kind"], registry=before).labels(kind="alpha").inc(5)
    Counter("events_total", "events", ["kind"], registry=after).labels(kind="alpha").inc(
        3
    )  # regression (lower)
    snap_before = registry_snapshot(before)
    snap_after = registry_snapshot(after)
    violations = assert_counter_monotonic(snap_before, snap_after)
    assert any(
        "events_total" in k for k in violations
    ), "Expected monotonic violation for events_total"


def test_registry_snapshot_monotonic_clean() -> None:
    before = CollectorRegistry()
    after = CollectorRegistry()
    Counter("jobs_processed_total", "jobs", registry=before).inc(10)
    Counter("jobs_processed_total", "jobs", registry=after).inc(12)
    vio = assert_counter_monotonic(registry_snapshot(before), registry_snapshot(after))
    assert vio == {}


def test_approximate_histogram_quantiles_multi() -> None:
    reg = CollectorRegistry()
    h = Histogram("latency_seconds", "latency", buckets=(0.1, 0.2, 0.5, 1.0), registry=reg)
    for v in [0.05, 0.07, 0.15, 0.18, 0.22, 0.3, 0.4, 0.8]:
        h.observe(v)
    qs = approximate_histogram_quantiles([0.5, 0.75, 0.9], "latency_seconds", registry=reg)
    assert set(qs.keys()) == {0.5, 0.75, 0.9}
    assert all(not math.isnan(val) for val in qs.values())
    assert qs[0.5] <= qs[0.75] <= qs[0.9]
