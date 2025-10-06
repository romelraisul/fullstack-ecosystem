import os
import sys

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def test_integration_summary_readiness_and_last_reload_present():
    with TestClient(app, base_url="http://localhost") as client:
        r = client.get("/systems/integration-summary")
        r.raise_for_status()
        summary = r.json()
        assert isinstance(summary, dict)

        # Required keys
        for key in ("total", "with_api_base", "with_health", "by_maturity"):
            assert key in summary

        total = int(summary.get("total", 0))
        with_health = int(summary.get("with_health", 0))

        # Readiness percentage should equal with_health / total (within 0..1)
        if total > 0:
            readiness_ratio = with_health / total
            assert 0.0 <= readiness_ratio <= 1.0
        else:
            assert with_health == 0

        # last_reload_at should be present and be a non-empty string (ISO timestamp)
        last_reload_at = summary.get("last_reload_at")
        assert isinstance(last_reload_at, str) and len(last_reload_at) > 0
