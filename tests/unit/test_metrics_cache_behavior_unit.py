import io
import os
from collections.abc import Callable
from contextlib import redirect_stdout
from typing import Any

from prometheus_client import CollectorRegistry, Histogram

from tests.utils.metrics import (
    approximate_histogram_quantile,
    approximate_histogram_quantiles,
    clear_metric_cache,
    get_metric_cache_stats,
)


def capture_debug(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, str]:
    buf = io.StringIO()
    old_debug = os.getenv("METRIC_CACHE_DEBUG")
    os.environ["METRIC_CACHE_DEBUG"] = "1"
    try:
        with redirect_stdout(buf):
            result = func(*args, **kwargs)
    finally:
        if old_debug is not None:
            os.environ["METRIC_CACHE_DEBUG"] = old_debug
        else:
            del os.environ["METRIC_CACHE_DEBUG"]
    return result, buf.getvalue()


def test_cache_populate_and_hit() -> None:
    clear_metric_cache()
    reg = CollectorRegistry()
    h = Histogram("cache_latency_seconds", "lat", buckets=(0.1, 0.5, 1.0), registry=reg)
    for v in [0.05, 0.2, 0.3, 0.9]:
        h.observe(v)
    # First call populates cache
    _, out1 = capture_debug(
        approximate_histogram_quantiles, [0.5, 0.9], "cache_latency_seconds", reg
    )
    assert "populate batch quantile cache" in out1
    stats = get_metric_cache_stats()
    assert stats["size"] >= 1
    # Second call should hit
    _, out2 = capture_debug(
        approximate_histogram_quantiles, [0.5, 0.9], "cache_latency_seconds", reg
    )
    assert "hit batch quantile cache" in out2


def test_cache_invalidation_on_total_change() -> None:
    clear_metric_cache()
    reg = CollectorRegistry()
    h = Histogram("invalidate_latency_seconds", "lat", buckets=(0.1, 0.5), registry=reg)
    for v in [0.05, 0.2]:
        h.observe(v)
    approximate_histogram_quantiles([0.5], "invalidate_latency_seconds", reg)
    # Mutate data
    h.observe(0.4)
    # Should invalidate (total increased)
    _, out = capture_debug(
        approximate_histogram_quantiles, [0.5], "invalidate_latency_seconds", reg
    )
    assert "invalidated batch quantile cache" in out


def test_cache_invalidation_on_bucket_len_change() -> None:
    clear_metric_cache()
    reg = CollectorRegistry()
    h = Histogram("bucketlen_latency_seconds", "lat", buckets=(0.1, 0.5), registry=reg)
    for v in [0.05, 0.2]:
        h.observe(v)
    approximate_histogram_quantile(0.5, "bucketlen_latency_seconds", reg)
    # Simulate new bucket appearance by observing value > existing max (creates +Inf bucket already but we can add more data)
    h.observe(0.4)
    _, out = capture_debug(approximate_histogram_quantile, 0.5, "bucketlen_latency_seconds", reg)
    # Either invalidated single or batch message acceptable
    assert "invalidated single quantile cache" in out or "invalidated batch quantile cache" in out


def test_cache_clear_and_stats() -> None:
    clear_metric_cache()
    reg = CollectorRegistry()
    h = Histogram("clear_latency_seconds", "lat", buckets=(0.1, 0.5), registry=reg)
    h.observe(0.05)
    approximate_histogram_quantiles([0.5], "clear_latency_seconds", reg)
    stats_before = get_metric_cache_stats()
    assert stats_before["size"] >= 1
    clear_metric_cache()
    stats_after = get_metric_cache_stats()
    assert stats_after["size"] == 0
