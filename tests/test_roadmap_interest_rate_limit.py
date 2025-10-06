from fastapi.testclient import TestClient

from backend.app.main import app


def test_roadmap_interest_rate_limit_exceeds():
    client = TestClient(app)
    # Ensure we start fresh (different IP simulation via header if needed)
    accepted = 0
    rejected = 0
    for i in range(7):  # attempt 7 submissions; limit is 5 per 5 min window
        payload = {"email": f"tester+{i}@example.com"}
        r = client.post("/api/roadmap-interest", json=payload)
        if r.status_code == 202:
            accepted += 1
        elif r.status_code == 429:
            rejected += 1
        else:
            raise AssertionError(f"Unexpected status {r.status_code} body={r.text}")
    assert accepted == 5, f"Expected 5 accepted submissions, got {accepted}"
    assert rejected >= 2, f"Expected at least 2 rejections, got {rejected}"
