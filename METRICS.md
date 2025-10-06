# Metrics Catalog

Central reference for first-class metrics exposed by the stack. Keep entries concise and actionable.

## Conventions

- Histogram base unit: seconds unless otherwise noted (`_seconds` suffix explicit).
- Counters end in `_total`.
- Gauges omit unit unless critical (e.g. `_ms`).
- Recording rules use namespace prefixes with colon separators for semantic grouping.

---

## Internal Latency Sampler (API)

Background task sampling internal dependency health endpoints every `LATENCY_SAMPLE_INTERVAL` seconds.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `internal_service_latency_seconds` | Histogram | `service`, `success` | Latency distribution of sampled health requests. `success`="true"/"false". Failures still observe duration. |
| `internal_service_latency_last_ms` | Gauge | `service` | Last successful latency (ms). Not updated on failure. |
| `internal_service_latency_class` | Gauge | `service` | Encoded qualitative class of last sample: good=0, warn=1, high=2, na=3. |
| `internal_service_latency_attempts_total` | Counter | `service` | Total sampling attempts. |
| `internal_service_latency_ok_total` | Counter | `service` | Successful sampling attempts. |
| `internal_service_latency_targets` | Gauge | `source` | Count of configured targets; `source`=`persisted` or `env`. |

### Derived Failure Rate

PromQL (5m window):

```promql
(1 - (sum by(service)(rate(internal_service_latency_ok_total[5m])) / sum by(service)(rate(internal_service_latency_attempts_total[5m]))))
```

Recording rules consolidate this into `internal_service:failure_rate_5m` and
`internal_service:failure_rate_10m` for dashboard & alert reuse.

### p99 Latency Recording Rules

Rules (examples):

```text
internal_service:p99_latency_seconds_5m
internal_service:p99_latency_seconds_30m
```

Used by latency burn & high latency alerts to prevent repeated `histogram_quantile` evaluations.

---

## Agent Fleet (Examples)

| Recording Rule | Purpose |
|----------------|---------|
| `agent:requests_rate_5m` | Unified 5m request rate per agent. |
| `agent:p95_latency_seconds_5m` | Aggregated p95 latency (5m) normalized to `agent` label. |
| `agent:error_rate_5m` | 5m 5xx error rate per agent vs total. |
| `agent:fleet:error_rate_5m` | Fleet-wide aggregated 5m 5xx error rate. |

Budget & burn rules leverage these to drive dynamic threshold alerts.

---

## Gauge: internal_service_latency_targets

Interpretation recap:

| Label `source` | Meaning |
|----------------|---------|
| `persisted` | Loaded from `backend/app/data/latency_targets.json` (admin persisted). |
| `env` | Loaded from `LATENCY_SAMPLE_TARGETS` env (default / ephemeral). |

Typical queries:

```promql
sum(internal_service_latency_targets)            # current count
count(internal_service_latency_targets)          # should be 1 (single source active)
```

Operational signal: shift from `persisted` to `env` unexpectedly may indicate file deletion or parse failure.

---

## Change Workflow

1. Add new metric to code with clear docstring & HELP text.
2. Update this catalog (keep table alphabetical within section if large).
3. If dashboards depend on it, add presence assertion in a unit test similar to `test_internal_failure_rate_recording.py`.
4. If reused heavily in alerts/dashboards: introduce a recording rule early.

---

## Future Candidates

- Unified `internal_service:failure_rate_{window}` for additional windows (30m, 1h) if burn detection expands.
- Fleet-level internal sampler failure rate gauge.
