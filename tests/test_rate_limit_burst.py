from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def test_rate_limit_burst():
    # Endpoint /api/v1/test/rate-limit-probe assumed to have very low limit (e.g., 2 per window)
    success = 0
    too_many = 0
    responses = []
    for _ in range(10):
        r = client.get("/api/v1/test/rate-limit-probe")
        responses.append(r.status_code)
        if r.status_code == 200:
            success += 1
        elif r.status_code == 429:
            too_many += 1
    # We expect at least one 429 if limit is functioning and fewer successes than attempts
    assert too_many >= 1, f"Expected at least one 429, got none. Statuses={responses}"
    assert success < 10, "All requests succeeded; rate limiting not enforced"
    # Check retry-after header present on a 429
    r2 = client.get("/api/v1/test/rate-limit-probe")
    if r2.status_code == 429:
        assert any(
            h.lower() == "retry-after" for h in r2.headers
        ), "Missing Retry-After header on 429"
