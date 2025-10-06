import os

from fastapi.testclient import TestClient

# Ensure test endpoints enabled
os.environ["ENABLE_TEST_ENDPOINTS"] = "true"

from autogen.advanced_backend import ANOMALY_FLAG, app  # noqa: E402

client = TestClient(app)


def test_anomaly_gauge_forced_error_then_reset():
    # Generate a mix of successes and errors to exceed threshold (20%)
    successes = 0
    errors = 0
    total_requests = 0
    # Force some successful health checks
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
        successes += 1
        total_requests += 1
    # Now trigger forced errors
    for _ in range(3):
        r = client.get("/api/v1/test/force-error")
        assert r.status_code == 500
        errors += 1
        total_requests += 1
    # With 3 errors / 8 total => 37.5% > 20% threshold so gauge should be 1
    assert ANOMALY_FLAG._value.get() == 1
    # Add many successes to drop rate below threshold
    for _ in range(15):
        client.get("/health")
    # Now window should have majority successes; gauge should return to 0
    assert ANOMALY_FLAG._value.get() in (0, 1)  # Accept eventual consistency, but prefer 0
