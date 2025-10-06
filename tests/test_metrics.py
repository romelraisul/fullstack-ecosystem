# Reuse the functions from the scripts module by importing via path
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate_taxonomy_metrics.py"
spec = importlib.util.spec_from_file_location("genmetrics", str(SCRIPT_PATH))
gm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gm)


def test_placeholder_detection():
    cases = [
        (None, True),
        ("", True),
        ("   ", True),
        ("TBD", True),
        ("todo: write runbook", True),
        ("placeholder", True),
        ("This is a real runbook", False),
        ("https://example.com/runbook", False),
    ]
    for text, expected in cases:
        assert gm.placeholder(text) is expected


def make_alert(created_delta_days=None, runbook=None):
    a = {"alert": "unit-test-alert", "created_at": None, "runbook": runbook}
    if created_delta_days is not None:
        dt = datetime.now(timezone.utc) - timedelta(days=created_delta_days)
        a["created_at"] = dt.isoformat()
    return a


def test_sla_computation():
    # Alert with created_at 5 days ago and a real runbook should produce sla_days=5
    alerts = [make_alert(5, "https://example.com/rb")]
    stats = gm.compute_runbook_sla(alerts)
    assert stats["count"] == 1
    assert stats["max_days"] == stats["median_days"] == stats["avg_days"]

    # If runbook is placeholder, SLA ignored
    alerts = [make_alert(3, "TBD")]
    stats = gm.compute_runbook_sla(alerts)
    assert stats["count"] == 0
    assert stats["median_days"] is None
