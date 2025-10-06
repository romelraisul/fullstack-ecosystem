"""Prometheus metrics testing helpers.

Functions:
    find_metric_lines(metric_name, text) -> list[str]
        Extract raw exposition lines that start with the metric name.

    assert_metric_present(metric, predicate=None, message=None, registry=None)
        Scrape the provided registry (or current default if None) and assert that
        one or more lines for the given metric exist and satisfy an optional
        predicate.

Design notes:
    * Kept dependency surface minimal (only pytest + prometheus_client when available)
    * Predicate pattern lets callers flexibly assert on label sets or values
    * Optional registry parameter enables tests that construct isolated CollectorRegistry
      instances without having to duplicate scrape parsing logic
    * Returns the matching lines to enable follow-on custom parsing when needed
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable, Iterable
from typing import (
    Any,
    TypedDict,
    cast,
)

try:  # pragma: no cover - import guarded for environments lacking prometheus_client
    from prometheus_client import generate_latest
    from prometheus_client.registry import CollectorRegistry
except Exception:  # pragma: no cover
    # Fallback lightweight stubs so type checking works even when library absent.
    class CollectorRegistry:  # type: ignore[no-redef]
        ...

    def generate_latest(registry: CollectorRegistry | None = None) -> bytes:
        return b""  # Empty exposition; callers typically skip on emptiness.


__all__ = [
    "find_metric_lines",
    "assert_metric_present",
    "assert_metric_absent",
    "scrape_metric_samples",
    "get_single_sample",
    "approximate_histogram_quantile",
    "metrics_diff",
    "filter_metrics_diff",
    "approximate_histogram_quantiles",
    "registry_snapshot",
    "assert_counter_monotonic",
    "assert_no_counter_regressions",
    "clear_metric_cache",
    "get_metric_cache_stats",
]


class MetricSample(TypedDict):
    """Structured representation of a scraped metric sample.

    Keys
    ----
    name: canonical metric name encountered in exposition (e.g. http_requests_total)
    labels: mapping of label -> value
    value: parsed numeric value (float('nan') if unparsable)
    raw: original exposition line for debugging
    """

    name: str
    labels: dict[str, str]
    value: float
    raw: str


def find_metric_lines(metric_name: str, text: str) -> list[str]:
    return [l for l in text.splitlines() if l.startswith(metric_name)]


def assert_metric_present(
    metric: str,
    predicate: Callable[[list[str]], bool] | None = None,
    message: str | None = None,
    registry: CollectorRegistry | None = None,
):
    """Assert that a metric is present in Prometheus exposition text.

    Parameters
    ----------
    metric : str
        Metric name prefix to locate (e.g. 'app_startups_total').
    predicate : Callable[[List[str]], bool] | None
        Optional predicate applied to the list of matching exposition lines.
        Defaults to truthiness (at least one line). If provided and returns
        False/Falsey the assertion fails.
    message : str | None
        Custom failure message to augment default output.
    registry : CollectorRegistry | None
        If supplied, scrape this registry instead of the process global default.
        Accepts either a fresh test-scoped registry or the default replacement
        fixture's instance. When None, the global default registry is used.
    """

    # prometheus-client>=0.20.0 supports passing a custom registry directly
    data = (
        generate_latest(registry).decode("utf-8")
        if registry is not None
        else generate_latest().decode("utf-8")
    )

    lines = find_metric_lines(metric, data)
    pred = predicate or (lambda ls: bool(ls))
    if not pred(lines):
        fail_msg = message or f"Metric '{metric}' not present or predicate failed"
        fail_msg += f"; lines: {lines}"
        raise AssertionError(fail_msg)
    return lines


def assert_metric_absent(
    metric: str,
    message: str | None = None,
    registry: CollectorRegistry | None = None,
):
    """Assert that a metric name has no exposition lines.

    Parameters
    ----------
    metric : str
        Metric name prefix that should not appear.
    message : str | None
        Optional custom failure message.
    registry : CollectorRegistry | None
        Registry to scrape (defaults to process global).
    """

    data = (
        generate_latest(registry).decode("utf-8")
        if registry is not None
        else generate_latest().decode("utf-8")
    )
    lines = find_metric_lines(metric, data)
    if lines:
        raise AssertionError(message or f"Metric '{metric}' unexpectedly present; lines: {lines}")
    return True


def scrape_metric_samples(
    metric: str,
    registry: CollectorRegistry | None = None,
    require_present: bool = True,
) -> list[MetricSample]:
    """Return a list of parsed samples for the given metric prefix.

    Provides a light-weight textual parse sufficient for test assertions.
    """
    # generate_latest always defined (stubbed if real import failed)
    data = (
        generate_latest(registry).decode("utf-8")
        if registry is not None
        else generate_latest().decode("utf-8")
    )
    lines = find_metric_lines(metric, data)
    if require_present and not lines:
        raise AssertionError(f"Metric '{metric}' not found; no lines scraped")
    samples: list[MetricSample] = []
    for line in lines:
        raw = line
        label_part: dict[str, str] = {}
        value_str: str | None = None
        if "{" in line:
            before, rest = line.split("{", 1)
            labels_section, value_str = rest.split("}", 1)
            for kv in labels_section.split(","):
                if not kv.strip() or "=" not in kv:
                    continue
                k, v = kv.split("=", 1)
                label_part[k.strip()] = v.strip().strip('"')
            value_str = value_str.strip()
            name_part = before.strip()
        else:
            parts = line.split()
            name_part = parts[0] if parts else metric
            if len(parts) >= 2:
                value_str = parts[-1]
        try:
            value = float(value_str) if value_str is not None else float("nan")
        except ValueError:
            value = float("nan")
        samples.append({"name": name_part, "labels": label_part, "value": value, "raw": raw})
    return samples


def get_single_sample(
    metric: str,
    registry: CollectorRegistry | None = None,
    match_labels: dict[str, str] | None = None,
    require_present: bool = True,
) -> MetricSample:
    """Convenience helper expecting exactly one matching sample.

    If match_labels provided, only samples whose labels include the specified
    key/value pairs are considered.
    """
    samples = scrape_metric_samples(metric, registry=registry, require_present=require_present)
    if not samples:
        return {"name": metric, "labels": {}, "value": float("nan"), "raw": ""}
    candidates = samples
    if match_labels:
        candidates = [
            s for s in samples if all(s["labels"].get(k) == v for k, v in match_labels.items())
        ]
    if len(candidates) != 1:
        raise AssertionError(
            f"Expected exactly one sample for '{metric}' with labels {match_labels}; found {len(candidates)}"
        )
    return candidates[0]


def approximate_histogram_quantile(
    q: float,
    metric_prefix: str,
    registry: CollectorRegistry | None = None,
    match_labels: dict[str, str] | None = None,
) -> float:
    """Approximate histogram quantile from _bucket counts.

    Linear interpolation within bucket; suitable for coarse test thresholds.
    Returns NaN if insufficient data.
    """
    if not (0 < q < 1):
        raise ValueError("q must be between 0 and 1")
    bucket_metric = f"{metric_prefix}_bucket"

    disable_cache = os.getenv("DISABLE_METRIC_CACHE") == "1"
    cache_key = (
        id(registry) if registry is not None else 0,
        bucket_metric,
        frozenset((match_labels or {}).items()),
    )
    _bounds_cache: dict[Any, tuple[list[tuple[float, float]], float, int]] = getattr(
        approximate_histogram_quantile, "_bounds_cache", {}
    )
    if not hasattr(approximate_histogram_quantile, "_bounds_cache"):
        approximate_histogram_quantile._bounds_cache = _bounds_cache
    debug = os.getenv("METRIC_CACHE_DEBUG") == "1"

    def load_bounds() -> tuple[list[tuple[float, float]], float, int]:
        samples = scrape_metric_samples(bucket_metric, registry=registry, require_present=False)
        if match_labels:
            samples = [
                s for s in samples if all(s["labels"].get(k) == v for k, v in match_labels.items())
            ]
        bounds_local: list[tuple[float, float]] = []
        for s in samples:
            le = s["labels"].get("le")
            if le is None:
                continue
            try:
                ub = float("inf") if le == "+Inf" else float(le)
            except ValueError:
                continue
            bounds_local.append((ub, s["value"]))
        bounds_local.sort(key=lambda x: x[0])
        last_total = bounds_local[-1][1] if bounds_local else float("nan")
        return bounds_local, last_total, len(bounds_local)

    if disable_cache:
        bounds, _last, _len = load_bounds()
    else:
        if cache_key in _bounds_cache:
            cached_bounds, cached_total, cached_len = _bounds_cache[cache_key]
            current_bounds, current_total, current_len = load_bounds()
            if not current_bounds:
                bounds = current_bounds
            elif current_total != cached_total or current_len != cached_len:
                _bounds_cache[cache_key] = (current_bounds, current_total, current_len)
                bounds = current_bounds
                if debug:
                    print(
                        f"[metric-cache] invalidated single quantile cache for {bucket_metric} (total or len changed)"
                    )
            else:
                bounds = cached_bounds
                if debug:
                    print(f"[metric-cache] hit single quantile cache for {bucket_metric}")
        else:
            new_bounds, new_total, new_len = load_bounds()
            _bounds_cache[cache_key] = (new_bounds, new_total, new_len)
            bounds = new_bounds
            if debug:
                print(f"[metric-cache] populate single quantile cache for {bucket_metric}")
    if not bounds:
        return float("nan")
    bounds.sort(key=lambda x: x[0])
    total = bounds[-1][1]
    if total <= 0:
        return float("nan")
    target = q * total
    prev_bound = 0.0
    prev_count = 0.0
    for ub, count in bounds:
        if count >= target:
            bucket_total = count - prev_count
            if bucket_total <= 0 or ub == prev_bound:
                return ub
            frac = (target - prev_count) / bucket_total
            if ub == float("inf"):
                return prev_bound
            return prev_bound + frac * (ub - prev_bound)
        prev_bound = ub
        prev_count = count
    return bounds[-1][0]


def approximate_histogram_quantiles(
    quantiles: Iterable[float],
    metric_prefix: str,
    registry: CollectorRegistry | None = None,
    match_labels: dict[str, str] | None = None,
) -> dict[float, float]:
    """Compute multiple approximate quantiles in a single bucket scan.

    Avoids repeated parsing for each q. Returns mapping q -> value (or NaN if unavailable).
    """
    qs = list(quantiles)
    for q in qs:
        if not (0 < q < 1):
            raise ValueError(f"Invalid quantile {q}; must be 0<q<1")
    bucket_metric = f"{metric_prefix}_bucket"
    disable_cache = os.getenv("DISABLE_METRIC_CACHE") == "1"
    cache_key = (
        id(registry) if registry is not None else 0,
        bucket_metric,
        frozenset((match_labels or {}).items()),
    )
    _bounds_cache: dict[Any, tuple[list[tuple[float, float]], float, int]] = getattr(
        approximate_histogram_quantile, "_bounds_cache", {}
    )  # reuse cache from single quantile
    if not hasattr(approximate_histogram_quantile, "_bounds_cache"):
        approximate_histogram_quantile._bounds_cache = _bounds_cache
    debug = os.getenv("METRIC_CACHE_DEBUG") == "1"

    def load_bounds() -> tuple[list[tuple[float, float]], float, int]:
        samples = scrape_metric_samples(bucket_metric, registry=registry, require_present=False)
        if match_labels:
            samples = [
                s for s in samples if all(s["labels"].get(k) == v for k, v in match_labels.items())
            ]
        bounds_local: list[tuple[float, float]] = []
        for s in samples:
            le = s["labels"].get("le")
            if le is None:
                continue
            try:
                ub = float("inf") if le == "+Inf" else float(le)
            except ValueError:
                continue
            bounds_local.append((ub, s["value"]))
        bounds_local.sort(key=lambda x: x[0])
        last_total = bounds_local[-1][1] if bounds_local else float("nan")
        return bounds_local, last_total, len(bounds_local)

    if disable_cache:
        bounds, _last, _len = load_bounds()
    else:
        if cache_key in _bounds_cache:
            cached_bounds, cached_total, cached_len = _bounds_cache[cache_key]
            current_bounds, current_total, current_len = load_bounds()
            if not current_bounds:
                bounds = current_bounds
            elif current_total != cached_total or current_len != cached_len:
                _bounds_cache[cache_key] = (current_bounds, current_total, current_len)
                bounds = current_bounds
                if debug:
                    print(
                        f"[metric-cache] invalidated batch quantile cache for {bucket_metric} (total or len changed)"
                    )
            else:
                bounds = cached_bounds
                if debug:
                    print(f"[metric-cache] hit batch quantile cache for {bucket_metric}")
        else:
            new_bounds, new_total, new_len = load_bounds()
            _bounds_cache[cache_key] = (new_bounds, new_total, new_len)
            bounds = new_bounds
            if debug:
                print(f"[metric-cache] populate batch quantile cache for {bucket_metric}")
    if not bounds:
        return {q: float("nan") for q in qs}
    bounds.sort(key=lambda x: x[0])
    total = bounds[-1][1]
    if total <= 0:
        return {q: float("nan") for q in qs}

    results: dict[float, float] = {}
    # For each quantile perform single forward pass - but since interpolation depends on cumulative,
    # we'll just iterate once per quantile using precomputed cumulative list.
    cumul: list[tuple[float, float, float]] = []  # (ub, cumulative_count, prev_count)
    prev = 0.0
    for ub, count in bounds:
        cumul.append((ub, count, prev))
        prev = count
    for q in qs:
        target = q * total
        val = bounds[-1][0]
        for ub, count, prev_count in cumul:
            if count >= target:
                bucket_total = count - prev_count
                if bucket_total <= 0 or ub == (prev_count and ub):  # defensive
                    val = ub
                    break
                if ub == float("inf"):
                    # cannot interpolate infinite bucket, fallback to previous finite upper bound
                    # find previous finite bound
                    prev_finite = 0.0
                    for ub2, _c2, _ in cumul:
                        if ub2 == ub:
                            break
                        prev_finite = ub2
                    val = prev_finite
                    break
                frac = (target - prev_count) / bucket_total
                # previous bound is previous tuple's ub (or 0.0)
                prev_bound = 0.0
                for ub2, _, _ in cumul:
                    if ub2 == ub:
                        break
                    prev_bound = ub2
                val = prev_bound + frac * (ub - prev_bound)
                break
        results[q] = val
    return results


def metrics_diff(
    before: CollectorRegistry,
    after: CollectorRegistry,
    metric_prefix: str | None = None,
    include_unchanged: bool = False,
    strict_counters: bool = False,
) -> dict[str, dict[str, Any]]:
    """Compute value deltas between two registries for matching samples.

    When strict_counters is True, any sample whose name ends with '_total' and
    whose value decreased raises AssertionError (counter regression). Histogram
    _count and _sum are treated similarly.
    """
    if generate_latest is None:  # pragma: no cover
        return {}

    def collect(reg: CollectorRegistry) -> list[MetricSample]:
        text = generate_latest(reg).decode("utf-8")
        lines = [l for l in text.splitlines() if l and not l.startswith("#")]
        samples: list[MetricSample] = []
        for line in lines:
            name_token = line.split(" ", 1)[0]
            if metric_prefix and not name_token.startswith(metric_prefix):
                continue
            parsed = scrape_metric_samples(name_token, registry=reg, require_present=False)
            for s in parsed:
                if s["raw"].startswith(name_token):
                    samples.append(s)
        return samples

    before_samples = collect(before)
    after_samples = collect(after)

    def key(s: MetricSample) -> tuple[str, tuple[tuple[str, str], ...]]:
        return s["name"], tuple(sorted(s["labels"].items()))

    bmap = {key(s): s for s in before_samples}
    amap = {key(s): s for s in after_samples}
    all_keys = set(bmap) | set(amap)
    out: dict[str, dict[str, Any]] = {}
    regressions: list[str] = []
    for k in all_keys:
        b = bmap.get(k)
        a = amap.get(k)
        vb = b["value"] if b else 0.0
        va = a["value"] if a else 0.0
        delta = va - vb
        name = (a or b)["name"]  # type: ignore[index]
        labels = (a or b)["labels"]  # type: ignore[index]
        if (
            strict_counters
            and delta < 0
            and (name.endswith("_total") or name.endswith("_count") or name.endswith("_sum"))
        ):
            label_repr = (
                "{" + ",".join(f"{lk}={lv}" for lk, lv in labels.items()) + "}" if labels else ""
            )
            regressions.append(f"{name}{label_repr}: {vb} -> {va}")
        if not include_unchanged and abs(delta) < 1e-12:
            continue
        label_repr = (
            "{" + ",".join(f"{lk}={lv}" for lk, lv in labels.items()) + "}" if labels else ""
        )
        key_str = name + label_repr
        out[key_str] = {
            "value_before": vb,
            "value_after": va,
            "delta": delta,
            "labels": labels,
        }
    if regressions:
        raise AssertionError("Counter regressions detected: " + "; ".join(regressions))
    return out


def registry_snapshot(registry: CollectorRegistry) -> list[MetricSample]:
    """Capture a snapshot (list of MetricSample) for all current metrics in a registry.

    Useful for diff operations or monotonic checks without re-scraping multiple times.
    """
    # generate_latest always defined (stubbed if real import failed)
    text = generate_latest(registry).decode("utf-8")
    samples: list[MetricSample] = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        name_token = line.split(" ", 1)[0]
        parsed = scrape_metric_samples(name_token, registry=registry, require_present=False)
        for s in parsed:
            if s["raw"].startswith(name_token):
                samples.append(s)
    return samples


def assert_counter_monotonic(
    before_snapshot: list[MetricSample],
    after_snapshot: list[MetricSample],
    metric_prefix: str | None = None,
) -> dict[str, dict[str, float]]:
    """Return counter/histogram monotonic violations instead of raising.

    Examines *_total, *_count, *_sum samples and returns mapping of sample-key -> {before, after, delta}
    for any that decreased. Empty dict means no violations.
    """

    def key(s: MetricSample) -> tuple[str, tuple[tuple[str, str], ...]]:
        return s["name"], tuple(sorted(s["labels"].items()))

    def is_counter(name: str) -> bool:
        return name.endswith("_total") or name.endswith("_count") or name.endswith("_sum")

    bmap = {
        key(s): s
        for s in before_snapshot
        if is_counter(s["name"]) and (not metric_prefix or s["name"].startswith(metric_prefix))
    }
    amap = {
        key(s): s
        for s in after_snapshot
        if is_counter(s["name"]) and (not metric_prefix or s["name"].startswith(metric_prefix))
    }
    violations: dict[str, dict[str, float]] = {}
    all_keys = set(bmap) & set(amap)
    for k in all_keys:
        b = bmap[k]
        a = amap[k]
        if a["value"] < b["value"] - 1e-12:
            name = a["name"]
            labels = a["labels"]
            label_repr = (
                "{" + ",".join(f"{lk}={lv}" for lk, lv in labels.items()) + "}" if labels else ""
            )
            violations[name + label_repr] = {
                "before": b["value"],
                "after": a["value"],
                "delta": a["value"] - b["value"],
            }
    return violations


def assert_no_counter_regressions(
    before: CollectorRegistry,
    after: CollectorRegistry,
    metric_prefix: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Assert that no counters/histogram accumulators decreased between registries.

    Wraps metrics_diff with strict_counters=True. Returns the diff (filtered
    by metric_prefix if provided) for potential further inspection.
    Raises AssertionError on any regression.
    """
    diff = metrics_diff(
        before, after, metric_prefix=metric_prefix, include_unchanged=False, strict_counters=True
    )
    if metric_prefix:
        diff = {k: v for k, v in diff.items() if k.startswith(metric_prefix)}
    return diff


def filter_metrics_diff(
    diff: dict[str, dict[str, Any]],
    prefix: str | None = None,
    label_pred: Callable[[dict[str, str]], bool] | None = None,
) -> dict[str, dict[str, Any]]:
    """Filter a metrics_diff result by metric name prefix and/or label predicate.

    Parameters
    ----------
    diff : dict
        Output from metrics_diff.
    prefix : str | None
        Only retain entries whose key (metric{labels}) starts with this prefix.
    label_pred : callable | None
        Function returning True to keep a given entry; receives labels dict.
    """
    out: dict[str, dict[str, Any]] = {}
    for k, meta in diff.items():
        if prefix and not k.startswith(prefix):
            continue
        if label_pred and not label_pred(meta.get("labels", {})):
            continue
        out[k] = meta
    return out


def clear_metric_cache() -> None:
    """Clear internal histogram bucket cache used by quantile helpers.

    Useful for test isolation or benchmarking scenarios where cache effects
    should be excluded. Safe no-op if cache absent.
    """
    if hasattr(approximate_histogram_quantile, "_bounds_cache"):
        with contextlib.suppress(Exception):
            delattr(approximate_histogram_quantile, "_bounds_cache")


def get_metric_cache_stats() -> dict[str, Any]:
    """Return lightweight stats for the histogram bucket cache.

    Provides: size (entries), keys (stringified), and optional detail counts.
    Safe if cache absent.
    """
    cache_raw = getattr(approximate_histogram_quantile, "_bounds_cache", None)
    if not cache_raw:
        return {"size": 0, "keys": []}
    # Best-effort typed cast; cache key structure: (registry_id:int, metric:str, labels:frozenset)
    cache = cast(
        dict[tuple[int, str, frozenset], tuple[list[tuple[float, float]], float, int]], cache_raw
    )
    keys: list[str] = []
    for k in cache:
        try:
            reg_id, metric, labels = k
            keys.append(f"registry={reg_id}:{metric}:{len(labels)}labels")
        except Exception:
            keys.append(str(k))
    return {"size": len(cache), "keys": keys}
