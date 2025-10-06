from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from tests.utils.metrics import scrape_metric_samples


def test_scrape_simple_gauge() -> None:
    reg = CollectorRegistry()
    g = Gauge("value_demo_gauge", "demo", registry=reg)
    g.set(3.14)
    samples = scrape_metric_samples("value_demo_gauge", registry=reg)
    assert len(samples) == 1
    assert samples[0]["value"] == 3.14


def test_scrape_labeled_counter() -> None:
    reg = CollectorRegistry()
    c = Counter("value_demo_total", "demo", ["kind"], registry=reg)
    c.labels(kind="alpha").inc(2)
    c.labels(kind="beta").inc(5)
    samples = scrape_metric_samples("value_demo_total", registry=reg)
    kinds = {s["labels"]["kind"] for s in samples}
    values = {s["labels"]["kind"]: s["value"] for s in samples}
    assert kinds == {"alpha", "beta"}
    assert values["alpha"] == 2
    assert values["beta"] == 5


def test_scrape_histogram_bucket_and_sum() -> None:
    reg = CollectorRegistry()
    h = Histogram(
        "value_demo_hist_seconds", "demo hist", registry=reg, buckets=(0.1, 0.5, 1.0, float("inf"))
    )
    # observe a few values
    for v in [0.05, 0.3, 0.7, 1.2]:
        h.observe(v)
    # ensure buckets show up
    bucket_samples = scrape_metric_samples("value_demo_hist_seconds_bucket", registry=reg)
    sum_samples = scrape_metric_samples("value_demo_hist_seconds_sum", registry=reg)
    count_samples = scrape_metric_samples("value_demo_hist_seconds_count", registry=reg)
    # Basic sanity assertions
    assert any(s["labels"].get("le") == "0.1" for s in bucket_samples)
    assert any(s["labels"].get("le") == "0.5" for s in bucket_samples)
    assert any(s["labels"].get("le") == "1.0" for s in bucket_samples)
    assert any(s["labels"].get("le") == "+Inf" for s in bucket_samples)
    assert sum_samples and sum_samples[0]["value"] > 0
    assert count_samples and count_samples[0]["value"] == 4


def test_scrape_absent_returns_empty_when_not_required() -> None:
    reg = CollectorRegistry()
    samples = scrape_metric_samples("nonexistent_metric_total", registry=reg, require_present=False)
    assert samples == []


def test_scrape_absent_raises_by_default() -> None:
    reg = CollectorRegistry()
    try:
        scrape_metric_samples("still_missing_total", registry=reg)
    except AssertionError:
        pass
    else:
        raise AssertionError("Expected AssertionError for missing metric")
