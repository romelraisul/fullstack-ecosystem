import re

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _metric_value(metrics_text: str, name: str, label_fragment: str = ""):
    pattern = (
        rf"^{re.escape(name)}{{1}}.*{re.escape(label_fragment)} *(?P<val>[0-9]+(?:\.[0-9]+)?)$"
    )
    for line in metrics_text.splitlines():
        if re.match(pattern, line):
            return float(re.match(pattern, line).group("val"))
    return None


def test_readiness_gauges_update_after_force_experimental(monkeypatch):
    # Capture initial metrics snapshot
    metrics_before = client.get("/metrics").text
    total_before = _metric_value(metrics_before, "ecosystem_systems_total")

    # Force all to experimental (triggers helper)
    resp = client.post("/admin/force-experimental")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 0

    # Fetch metrics again
    metrics_after = client.get("/metrics").text
    total_after = _metric_value(metrics_after, "ecosystem_systems_total")
    assert total_after is not None
    # Total should remain consistent (inventory count) but gauge must exist
    if total_before is not None:
        assert total_after == total_before

    # Verify maturity metric for experimental exists and non-negative
    # (labels may appear like ecosystem_systems_maturity_count{maturity="experimental"} 12)
    assert "ecosystem_systems_maturity_count" in metrics_after
    assert 'maturity="experimental"' in metrics_after

    # Exercise systems_integration_summary which also invokes helper
    si = client.get("/systems/integration-summary")
    assert si.status_code == 200
    metrics_final = client.get("/metrics").text
    # Presence of with_api / with_health gauges updated
    assert "ecosystem_systems_with_api" in metrics_final
    assert "ecosystem_systems_with_health" in metrics_final
