from fastapi.testclient import TestClient

try:
    from autogen.advanced_backend import app  # type: ignore
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent / "autogen"))
    from advanced_backend import app  # type: ignore

client = TestClient(app)


def test_latency_distribution_and_quantiles_structures():
    # Hit a simple endpoint a few times to generate samples (adaptive must be enabled via env for collection)
    for _ in range(5):
        client.get("/api/version")
    dist = client.get("/api/v2/latency/distribution")
    assert dist.status_code == 200
    body = dist.json()
    assert "endpoints" in body
    # Quantiles endpoint
    q = client.get("/api/v2/latency/quantiles")
    assert q.status_code == 200
    qbody = q.json()
    assert "endpoints" in qbody
    # Structure validations (may be empty if adaptive disabled)
    if body["endpoints"]:
        for _ep, data in body["endpoints"].items():
            assert "p95_ms" in data
            assert "classes" in data
    if qbody["endpoints"]:
        for _ep, data in qbody["endpoints"].items():
            for k in ["p50_ms", "p90_ms", "p95_ms", "p99_ms"]:
                assert k in data
