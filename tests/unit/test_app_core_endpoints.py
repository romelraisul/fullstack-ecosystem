import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import _classify_latency_ms, _parse_latency_targets, app


@pytest.fixture(scope="module")
def client():
    # Use context manager form to ensure lifespan startup/shutdown executes
    with TestClient(app) as c:
        yield c


def test_root_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("service") == "ecosystem-api"


def test_health_sets_gauge(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_systems_list_initial(client):
    r = client.get("/systems")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.parametrize(
    "value,expected",
    [
        (-1, "na"),
        (0, "good"),
        (150, "good"),
        (151, "warn"),
        (400, "warn"),
        (401, "high"),
    ],
)
def test_classify_latency(value, expected):
    assert _classify_latency_ms(value) == expected


def test_parse_latency_targets():
    raw = "api:http://api/health, bad, grafana:http://grafana/health ,empty:"
    parsed = _parse_latency_targets(raw)
    names = {t["name"] for t in parsed}
    assert names == {"api", "grafana"}


@pytest.mark.parametrize("persist", [False, True])
def test_admin_set_latency_targets(client, tmp_path, persist, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    latency_file = data_dir / "latency_targets.json"
    monkeypatch.setattr("backend.app.main.LATENCY_TARGETS_FILE", str(latency_file))
    body = {"targets": [{"name": "svc1", "url": "http://svc1/health"}], "persist": persist}
    r = client.post("/admin/latency-targets", json=body)
    assert r.status_code == 200
    info = r.json()
    assert info["count"] == 1
    if persist:
        assert latency_file.exists()


def test_admin_force_experimental(client):
    r = client.post("/admin/force-experimental")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data


def test_admin_reload_inventory_failure(monkeypatch, client, tmp_path):
    # Force open() for the inventory file to raise FileNotFoundError to exercise error path
    import builtins

    original_open = builtins.open

    def failing_open(path, *args, **kwargs):
        if isinstance(path, str) and path.endswith("systems_inventory.json"):
            raise FileNotFoundError("forced missing for test")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)
    r = client.post("/admin/reload-inventory")
    # Expect 500 due to forced FileNotFoundError
    assert r.status_code == 500


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    # Check a sampling of expected metric names appear
    for expected in [
        "app_startups_total",
        "internal_service_latency_targets",
        "ecosystem_events_emitted_total",
    ]:
        assert expected in text
