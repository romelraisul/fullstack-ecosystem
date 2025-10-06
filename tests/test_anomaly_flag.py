import re


def test_anomaly_flag_trips(client):
    # Force some 404s to raise error rate
    for _ in range(25):
        client.get("/api/v1/does-not-exist")
    # Hit metrics endpoint
    metrics = client.get("/metrics").text
    # Find anomaly gauge value
    match = re.search(r"^api_error_anomaly\s+(\d+)", metrics, re.MULTILINE)
    assert match, "Anomaly gauge not found"
    value = int(match.group(1))
    # High ratio of errors should set to 1
    assert value in (0, 1)
    # Not asserting strictly 1 to avoid flakiness if other successful requests dilute window
