from fastapi.testclient import TestClient

from backend.app.main import app


def _counter_value(metrics_text: str, metric: str, label_fragment: str) -> float:
    for line in metrics_text.splitlines():
        if line.startswith(metric) and label_fragment in line:
            try:
                return float(line.rsplit(" ", 1)[-1])
            except Exception:
                continue
    return 0.0


def test_execute_policy_block_increment(monkeypatch, set_inventory):
    # Experimental system
    set_inventory([{"slug": "exp-system", "maturity": "experimental", "api_base": "/api"}])
    client = TestClient(app)
    metrics_before = client.get("/metrics").text
    before_val = _counter_value(
        metrics_before, "ecosystem_policy_blocks_total", 'system_slug="exp-system"'
    )

    # Call without required flag -> should 403 and increment counter
    r_forbidden = client.post("/system/exp-system/execute", json={"event": "test.event"})
    assert r_forbidden.status_code == 403

    metrics_mid = client.get("/metrics").text
    mid_val = _counter_value(
        metrics_mid, "ecosystem_policy_blocks_total", 'system_slug="exp-system"'
    )
    assert mid_val == before_val + 1

    # Call with flag -> accepted
    r_ok = client.post(
        "/system/exp-system/execute",
        headers={"X-Feature-Flag": "allow-experimental"},
        json={"event": "test.event"},
    )
    assert r_ok.status_code == 200
    metrics_after = client.get("/metrics").text
    after_val = _counter_value(
        metrics_after, "ecosystem_policy_blocks_total", 'system_slug="exp-system"'
    )
    # Counter should not increment again on allowed call
    assert after_val == mid_val
