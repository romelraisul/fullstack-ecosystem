from __future__ import annotations

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram

from tests.utils.metrics import filter_metrics_diff, metrics_diff


def test_metrics_diff_strict_counters_pass() -> None:
    before = CollectorRegistry()
    after = CollectorRegistry()
    c1b = Counter("jobs_processed_total", "jobs", ["queue"], registry=before)
    c1a = Counter("jobs_processed_total", "jobs", ["queue"], registry=after)
    c1b.labels(queue="fast").inc(5)
    c1a.labels(queue="fast").inc(7)  # increase
    diff = metrics_diff(before, after, strict_counters=True)
    assert any(v["delta"] == 2.0 for v in diff.values())


def test_metrics_diff_strict_counters_regression() -> None:
    before = CollectorRegistry()
    after = CollectorRegistry()
    c1b = Counter("drops_total", "drops", ["type"], registry=before)
    c1a = Counter("drops_total", "drops", ["type"], registry=after)
    c1b.labels(type="net").inc(10)
    c1a.labels(type="net").inc(5)  # lower than before
    with pytest.raises(AssertionError):
        metrics_diff(before, after, strict_counters=True)


def test_metrics_diff_filtering() -> None:
    before = CollectorRegistry()
    after = CollectorRegistry()
    cb = Counter("alpha_events_total", "alpha", registry=before)
    ca = Counter("alpha_events_total", "alpha", registry=after)
    cb.inc(3)
    ca.inc(8)
    hb = Histogram("latency_seconds", "lat", registry=before)
    ha = Histogram("latency_seconds", "lat", registry=after)
    hb.observe(0.1)
    ha.observe(0.2)
    ha.observe(0.4)
    diff = metrics_diff(before, after, include_unchanged=False)
    # Filter only alpha metrics
    filtered = filter_metrics_diff(diff, prefix="alpha_events_total")
    assert filtered and all(k.startswith("alpha_events_total") for k in filtered)
    # Filter by label predicate (none here will match arbitrary predicate)
    none = filter_metrics_diff(diff, label_pred=lambda lbls: lbls.get("queue") == "missing")
    assert none == {}
