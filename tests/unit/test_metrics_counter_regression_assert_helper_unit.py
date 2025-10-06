from __future__ import annotations

import pytest
from prometheus_client import CollectorRegistry, Counter

from tests.utils.metrics import assert_no_counter_regressions


def test_assert_no_counter_regressions_pass() -> None:
    reg_before = CollectorRegistry()
    reg_after = CollectorRegistry()
    c_before = Counter("example_events_total", "Example events", registry=reg_before)
    c_after = Counter("example_events_total", "Example events", registry=reg_after)

    c_before.inc(3)
    c_after.inc(5)

    # Should not raise
    diff = assert_no_counter_regressions(reg_before, reg_after, metric_prefix="example")
    assert any(k.startswith("example_events_total") for k in diff)


def test_assert_no_counter_regressions_fail() -> None:
    reg_before = CollectorRegistry()
    reg_after = CollectorRegistry()
    c_before = Counter("another_events_total", "Another events", registry=reg_before)
    c_after = Counter("another_events_total", "Another events", registry=reg_after)

    c_before.inc(10)
    c_after.inc(4)  # regression

    with pytest.raises(AssertionError):
        assert_no_counter_regressions(reg_before, reg_after, metric_prefix="another")


def test_assert_no_counter_regressions_unfiltered() -> None:
    reg_before = CollectorRegistry()
    reg_after = CollectorRegistry()
    c_before = Counter("mixed_counter_total", "Mixed counter", registry=reg_before)
    c_after = Counter("mixed_counter_total", "Mixed counter", registry=reg_after)

    c_before.inc(2)
    c_after.inc(3)

    diff = assert_no_counter_regressions(reg_before, reg_after)
    assert any(k.startswith("mixed_counter_total") for k in diff)
