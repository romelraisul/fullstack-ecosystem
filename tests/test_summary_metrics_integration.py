import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "autogen" / "ultimate_enterprise_summary.py"


def _import_summary_module():
    spec = importlib.util.spec_from_file_location("ultimate_summary", SUMMARY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_metrics_endpoint_contains_fleet_gauge():
    mod = _import_summary_module()
    app = mod.UltimateEnterpriseSummary().app
    # Use FastAPI test client without adding dependency (lightweight pattern)
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        import pytest

        pytest.skip("fastapi.testclient not available")
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert (
        "agent_fleet_error_budget_fraction" in body
    ), "Fleet error budget gauge missing from /metrics output"
