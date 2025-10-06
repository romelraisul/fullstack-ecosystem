import json
import os
import statistics
import time

from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)

# Basic performance smoke test (does not enforce tight SLA, just sanity)


def test_performance_smoke():
    latencies = []
    iterations = 20
    for _ in range(iterations):
        start = time.perf_counter()
        r = client.get("/api/v1/health")
        elapsed = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        latencies.append(elapsed)
    p95 = statistics.quantiles(latencies, n=100)[94]  # 95th percentile
    avg = sum(latencies) / len(latencies)
    # Soft expectations (tunable): p95 < 250ms, avg < 150ms for local test environment
    assert p95 < 500, f"p95 too high: {p95:.2f}ms (latencies={latencies})"
    assert avg < 300, f"Average latency high: {avg:.2f}ms"
    metrics = {
        "iterations": iterations,
        "avg_ms": avg,
        "p95_ms": p95,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "all_ms": latencies,
    }
    out_dir = os.environ.get("PERF_METRICS_DIR", "perf-metrics")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "performance_smoke.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
