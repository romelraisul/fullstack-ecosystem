from __future__ import annotations

import math

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram

from tests.utils.metrics import (
    approximate_histogram_quantile,
    get_single_sample,
    metrics_diff,
)


def test_get_single_sample_basic() -> None:
    reg = CollectorRegistry()
    Counter("demo_events_total", "demo counter", ["kind"], registry=reg).labels(kind="alpha").inc()
    sample = get_single_sample("demo_events_total", registry=reg, match_labels={"kind": "alpha"})
    assert sample["name"] == "demo_events_total"
    assert sample["labels"] == {"kind": "alpha"}
    assert sample["value"] == 1.0


def test_get_single_sample_raises_multiple() -> None:
    reg = CollectorRegistry()
    c = Counter("multi_events_total", "multi counter", ["k"], registry=reg)
    c.labels(k="a").inc()
    c.labels(k="b").inc()
    with pytest.raises(AssertionError):
        get_single_sample("multi_events_total", registry=reg)


def test_histogram_quantile_simple() -> None:
    reg = CollectorRegistry()
    h = Histogram("request_latency_seconds", "latency", buckets=(0.1, 0.5, 1.0), registry=reg)
    # Observe values: some fast, some slower
    for v in [0.05, 0.07, 0.2, 0.3, 0.4, 0.55, 0.6, 0.9]:
        h.observe(v)
    p50 = approximate_histogram_quantile(0.5, "request_latency_seconds", registry=reg)
    assert 0.05 <= p50 <= 0.6
    p90 = approximate_histogram_quantile(0.9, "request_latency_seconds", registry=reg)
    assert p90 >= p50


def test_metrics_diff_counter_and_histogram() -> None:
    reg_before = CollectorRegistry()
    reg_after = CollectorRegistry()
    Counter("tx_total", "transactions", ["type"], registry=reg_before).labels(type="read").inc(3)
    c_after = Counter("tx_total", "transactions", ["type"], registry=reg_after)
    c_after.labels(type="read").inc(8)
    c_after.labels(type="write").inc(2)
    # histogram in after only
    h_after = Histogram(
        "payload_size_bytes", "payload size", buckets=(100, 500), registry=reg_after
    )
    for sz in [50, 60, 120, 300, 800]:
        h_after.observe(sz)

    diff = metrics_diff(reg_before, reg_after, metric_prefix=None)
    # Expect read delta 5, write delta 2
    tx_entries = {k: v for k, v in diff.items() if k.startswith("tx_total")}
    assert any(abs(meta["delta"] - 5.0) < 1e-9 for meta in tx_entries.values())
    assert any(abs(meta["delta"] - 2.0) < 1e-9 for meta in tx_entries.values())
    size_entries = {k: v for k, v in diff.items() if k.startswith("payload_size_bytes")}
    assert size_entries  # some bucket/sum/count deltas


def test_histogram_quantile_no_data() -> None:
    reg = CollectorRegistry()
    q = approximate_histogram_quantile(0.5, "empty_histogram", registry=reg)
    assert math.isnan(q)
