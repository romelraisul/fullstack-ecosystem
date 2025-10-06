import re

from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def test_rate_limit_probe_endpoint_hits_and_blocks():
    # Perform 3 allowed requests
    successes = 0
    for _ in range(3):
        r = client.get("/api/v1/test/rate-limit")
        assert r.status_code == 200
        successes += 1
    # 4th should rate limit (429)
    r = client.get("/api/v1/test/rate-limit")
    assert r.status_code == 429, f"Expected 429 after limit exceeded, got {r.status_code}"  # type: ignore


def test_metrics_route_template_labels_present():
    # Hit a parameterized endpoint (create workflow then execution status)
    # We mock auth dependencies elsewhere; for now just call root and metrics
    r_root = client.get("/health")
    assert r_root.status_code == 200
    # Access metrics endpoint
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    body = metrics_resp.text
    # Assert that http_requests_total lines use templated path e.g. /health not expanded dynamic segments
    # Since we did not call dynamic endpoints here, just assert presence of method label
    assert "http_requests_total" in body
    assert 'endpoint="/health"' in body or 'endpoint="/metrics"' in body
    # Basic sanity: no obvious high cardinality raw query strings
    assert "?" not in re.findall(r'endpoint="([^"]+)"', body)[0]
