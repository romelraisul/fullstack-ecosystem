# Test Utilities

This directory contains shared helper utilities for tests.

## Files

- `metrics.py` – Helpers for asserting Prometheus metrics are exposed.

## Usage

```python
from prometheus_client import CollectorRegistry, Counter
from tests.utils.metrics import assert_metric_present, assert_metric_absent

# After exercising code that should emit `my_metric_total` in the default test registry
assert_metric_present('my_metric_total')

# With a custom predicate (e.g. specific label present)
assert_metric_present(
    'internal_service_latency_targets',
    predicate=lambda lines: any('source="env"' in l for l in lines),
    message='env source label missing'
)

# Using an isolated registry (unit-level synthetic counters)
reg = CollectorRegistry()
Counter('example_total', 'demo', ['kind'], registry=reg).labels(kind='alpha').inc()
assert_metric_present('example_total', registry=reg)

# Negative assertion (ensure something was NOT emitted)
assert_metric_absent('should_not_exist_total', registry=reg)
```

### Parameters (assert_metric_present)

### Function: assert_metric_absent

Simple convenience to fail if any exposition line begins with the provided metric name.
Useful for validating cleanup flows or ensuring deprecated metrics are no longer exported.

```python
from tests.utils.metrics import assert_metric_absent

assert_metric_absent('deprecated_metric_total')
```

| Name | Type | Default | Purpose |
|------|------|---------|---------|
| metric | str | (required) | Metric name prefix to search for in exposition lines |
| predicate | Callable[[list[str]], bool] | None | Custom test on the collected lines (defaults to at least one) |
| message | str | None | Custom failure message (appends matched lines) |
| registry | CollectorRegistry | None | Scrape this registry instead of global default (supports isolated unit registries) |

### Function: scrape_metric_samples

Parses matching metric exposition lines into structured samples:

```python
from prometheus_client import CollectorRegistry, Counter
from tests.utils.metrics import scrape_metric_samples

reg = CollectorRegistry()
c = Counter('orders_total', 'demo', ['status'], registry=reg)
c.labels(status='ok').inc(3)
c.labels(status='fail').inc(1)
samples = scrape_metric_samples('orders_total', registry=reg)
by_status = {s['labels']['status']: s['value'] for s in samples}
assert by_status == {'ok': 3.0, 'fail': 1.0}
```

Returns: list of TypedDict `MetricSample` objects with keys: `name`, `labels`, `value`, `raw`.

Set `require_present=False` to return an empty list instead of raising when metric is absent.

### Function: get_single_sample

Convenience wrapper returning exactly one parsed sample (optionally filtered by
label matches). Raises `AssertionError` if zero or more than one match.

```python
from tests.utils.metrics import get_single_sample
sample = get_single_sample('orders_total', registry=reg, match_labels={'status': 'ok'})
assert sample['value'] == 3.0
```

If `require_present=False` and no sample matches, a placeholder sample with `value=NaN` is returned.

### Function: approximate_histogram_quantile

Approximates a quantile for a histogram using `_bucket` cumulative counts via
simple linear interpolation inside the containing bucket.

```python
from prometheus_client import Histogram
from tests.utils.metrics import approximate_histogram_quantile

h = Histogram('request_latency_seconds', 'latency', buckets=(0.1, 0.5, 1.0), registry=reg)
for v in [0.05, 0.07, 0.2, 0.9]:
    h.observe(v)
p90 = approximate_histogram_quantile(0.9, 'request_latency_seconds', registry=reg)
assert p90 < 1.0
```

Returns `float('nan')` if no bucket data present. Intended for coarse
assertions (e.g. p95 < threshold) in unit tests, not production SLIs.

### Function: approximate_histogram_quantiles

Batch variant computing multiple quantiles with a single bucket scan.

```python
from tests.utils.metrics import approximate_histogram_quantiles
qs = approximate_histogram_quantiles([0.5, 0.9, 0.99], 'request_latency_seconds', registry=reg)
assert 0.5 in qs and 0.9 in qs and 0.99 in qs
```

### Function: registry_snapshot

Captures all current samples in a registry into a list of `MetricSample`, suitable for
passing to diff / monotonic utilities without repeated scrapes.

```python
from tests.utils.metrics import registry_snapshot
snap = registry_snapshot(reg)
assert any(s['name'].startswith('orders_') for s in snap)
```

### Function: assert_counter_monotonic

Soft check returning a mapping of counter/histogram series that decreased between two snapshots.
Empty dict indicates no regressions.

```python
from tests.utils.metrics import assert_counter_monotonic
before = registry_snapshot(reg_before)
after = registry_snapshot(reg_after)
violations = assert_counter_monotonic(before, after, metric_prefix='jobs_')
if violations:
    # optional: log or assert depending on strictness level
    print('Regressions:', violations)
```

### Function: assert_no_counter_regressions

Hard assertion variant that raises immediately if any counter / histogram accumulator
(`*_total`, `*_count`, `*_sum`) decreases between two registries. Internally wraps
`metrics_diff(..., strict_counters=True)`. Returns the produced diff (minus unchanged entries)
for optional inspection when no regressions occur.

```python
from prometheus_client import Counter, CollectorRegistry
from tests.utils.metrics import assert_no_counter_regressions

before = CollectorRegistry(); after = CollectorRegistry()
cb = Counter('events_total', 'events', registry=before)
ca = Counter('events_total', 'events', registry=after)
cb.inc(10); ca.inc(12)
diff = assert_no_counter_regressions(before, after, metric_prefix='events_')
assert any(k.startswith('events_total') for k in diff)
```

If a regression is detected an `AssertionError` lists each offending series with its before/after values.

### Function: metrics_diff

Computes deltas between two `CollectorRegistry` snapshots over matching metric samples.

```python
from prometheus_client import Counter, CollectorRegistry
from tests.utils.metrics import metrics_diff

before = CollectorRegistry(); after = CollectorRegistry()
c_before = Counter('jobs_processed_total', 'jobs', ['queue'], registry=before)
c_after = Counter('jobs_processed_total', 'jobs', ['queue'], registry=after)
c_before.labels(queue='fast').inc(5)
c_after.labels(queue='fast').inc(8)
diff = metrics_diff(before, after, strict_counters=True)
entry = next(v for k,v in diff.items() if k.startswith('jobs_processed_total'))
assert entry['delta'] == 3.0
```

Parameters of note:

- `metric_prefix`: restrict to metrics starting with the prefix.
- `include_unchanged`: include zero-delta entries (default False).
- `strict_counters`: when True, any decrease in `*_total`, `*_count`, or `*_sum` raises AssertionError.

### Function: filter_metrics_diff

Filters a `metrics_diff` result by optional name prefix and/or label predicate.

```python
from tests.utils.metrics import filter_metrics_diff
only_jobs = filter_metrics_diff(diff, prefix='jobs_processed_total')
fast_only = filter_metrics_diff(diff, label_pred=lambda lbls: lbls.get('queue') == 'fast')
```

Returns a pruned dict preserving original diff entry structures.

## Rationale

Centralizes repeated scraping / assertion logic to keep individual tests concise
and consistent, and avoids copy/paste of generate_latest parsing.

The optional `registry` parameter enables assertions against synthetic
registries created inside a test (e.g. validating counter math without
touching global process metrics) while retaining identical ergonomics.

The diff / quantile helpers extend this ergonomics into time-delta and percentile
style assertions while keeping parsing logic centralized and intentionally light-weight.

## Related Tooling

- `make ensure-pythonpath` – Verifies `sitecustomize.py` path injection and that utilities
    (including this module) import correctly.
- `scripts/start_unified_dashboard.py` – Wrapper to launch the unified FastAPI operations dashboard (see root README).
