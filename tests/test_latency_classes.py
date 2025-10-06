import re

from fastapi.testclient import TestClient

# Import the app
try:
    from autogen.advanced_backend import app  # type: ignore
except ModuleNotFoundError:  # Fallback if tests run from repo root without package install
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent / "autogen"))
    from advanced_backend import app  # type: ignore

client = TestClient(app)


def test_latency_class_counter_increments():
    # Perform a couple of requests to a lightweight endpoint (metrics excluded to avoid recursion)
    r1 = client.get("/metrics")  # warm-up to load metrics
    assert r1.status_code == 200
    r2 = (
        client.get("/api/version")
        if client.get("/api/version").status_code == 200
        else client.get("/metrics")
    )
    assert r2.status_code == 200
    r3 = client.get("/metrics")
    text = r3.text
    # Look for at least one latency class metric line
    # Pattern: http_latency_class_total{method="GET",endpoint="/api/version",latency_class="sub50"} 1.0
    pattern = re.compile(
        r'^http_latency_class_total\{.*latency_class="[^"]+".*\} \d+(?:\.\d+)?$', re.MULTILINE
    )
    matches = pattern.findall(text)
    assert (
        matches
    ), f"Expected at least one latency class metric line. Metrics snippet: {text[:500]}"
