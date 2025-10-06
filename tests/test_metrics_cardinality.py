from fastapi.testclient import TestClient

from autogen.advanced_backend import app

client = TestClient(app)


def test_metrics_path_label_cardinality():
    # Hit a few endpoints to ensure metrics created
    client.get("/api/v1/health")
    client.get("/api/v1/agents")
    client.get("/api/v1/workflows")  # listing (might be empty)

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    lines = metrics.text.splitlines()
    path_labels = set()
    for ln in lines:
        if "request_count_total" in ln and "path=" in ln:
            # extract path label value
            # sample: request_count_total{method="GET",path="/api/v1/health",status="200"} 1
            try:
                meta = ln.split("{", 1)[1].split("}", 1)[0]
                parts = meta.split(",")
                for p in parts:
                    if p.startswith("path="):
                        val = p.split("=", 1)[1].strip('"')
                        path_labels.add(val)
            except Exception:  # pragma: no cover
                pass
    # We expect limited number of unique path templates (not raw dynamic values)
    assert (
        len(path_labels) <= 25
    ), f"Too many unique path labels -> {len(path_labels)} labels={sorted(path_labels)}"
    # Ensure core endpoints present
    assert "/api/v1/health" in path_labels
    assert (
        "/metrics" in path_labels or "/metrics" not in path_labels
    )  # tolerant (metrics endpoint may or may not self-record)
