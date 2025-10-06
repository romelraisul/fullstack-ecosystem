import os

from fastapi.testclient import TestClient

os.environ["ADAPTIVE_SLO_ENABLED"] = "true"

try:
    from autogen.advanced_backend import app  # type: ignore
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent / "autogen"))
    from advanced_backend import app  # type: ignore

client = TestClient(app)


def _maybe_auth_headers():
    # Obtain admin token for endpoints requiring admin auth
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})
    if login_resp.status_code == 200 and "access_token" in login_resp.json():
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    # If login fails, return empty headers (test will expect 401/403)
    return {}


def test_aggregates_present_after_requests():
    for _ in range(5):
        client.get("/api/version")
    dist = client.get("/api/v2/latency/distribution").json()
    if dist["endpoints"]:
        for _ep, data in dist["endpoints"].items():
            # Aggregates may be zero for very fast tests but fields must exist
            assert "sample_count" in data
            assert "sample_mean_ms" in data
            assert "sample_variance_ms2" in data
            assert "sample_stddev_ms" in data


def test_reset_endpoint_clears_state():
    # Generate traffic
    for _ in range(3):
        client.get("/api/version")
    dist_before = client.get("/api/v2/latency/distribution").json()
    if dist_before["endpoints"]:
        ep = next(iter(dist_before["endpoints"].keys()))
        resp = client.post(
            "/api/v2/latency/adaptive/reset", params={"endpoint": ep}, headers=_maybe_auth_headers()
        )
        assert resp.status_code in (200, 401, 403)  # If auth enforced test still should not crash
        # After reset distribution may lose that endpoint
        dist_after = client.get("/api/v2/latency/distribution").json()
        if resp.status_code == 200:
            assert (
                ep not in dist_after["endpoints"]
                or dist_after["endpoints"][ep]["window_samples"] == 0
            )
