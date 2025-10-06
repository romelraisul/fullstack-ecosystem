from __future__ import annotations

import pytest
from prometheus_client import CollectorRegistry, Counter, Gauge

from tests.utils.metrics import assert_metric_absent, assert_metric_present


def test_assert_metric_present_with_custom_registry() -> None:
    reg = CollectorRegistry()
    counter = Counter("helper_demo_total", "demo counter", ["kind"], registry=reg)
    counter.labels(kind="alpha").inc()

    lines = assert_metric_present("helper_demo_total", registry=reg)
    assert any('kind="alpha"' in l for l in lines)


def test_assert_metric_absent_with_custom_registry() -> None:
    reg = CollectorRegistry()
    # Do not register metric with the name 'nonexistent_metric_total'
    assert_metric_absent("nonexistent_metric_total", registry=reg)


def test_assert_metric_absent_fails_when_present() -> None:
    reg = CollectorRegistry()
    gauge = Gauge("unexpected_gauge", "demo gauge", registry=reg)
    gauge.set(5)
    with pytest.raises(AssertionError):
        assert_metric_absent("unexpected_gauge", registry=reg)


def test_assert_metric_present_predicate_failure() -> None:
    reg = CollectorRegistry()
    counter = Counter("predicate_demo_total", "demo", ["kind"], registry=reg)
    counter.labels(kind="x").inc()
    # Predicate expects label kind="y" which is absent
    with pytest.raises(AssertionError):
        assert_metric_present(
            "predicate_demo_total",
            predicate=lambda lines: any('kind="y"' in l for l in lines),
            registry=reg,
        )
