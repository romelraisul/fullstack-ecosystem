from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_latency_targets_non_object_body():
    r = client.post("/admin/latency-targets", json=[{"name": "x", "url": "http://x"}])
    assert r.status_code in (400, 422)


def test_latency_targets_empty_list():
    r = client.post("/admin/latency-targets", json={"targets": []})
    assert r.status_code == 400
    assert "targets" in r.text.lower()


def test_latency_targets_all_invalid_entries():
    body = {"targets": ["not-a-dict", 123, {"name": "", "url": ""}]}
    r = client.post("/admin/latency-targets", json=body)
    assert r.status_code == 400
    assert "no valid targets" in r.text.lower()


def test_latency_targets_mixed_valid_and_invalid():
    body = {
        "targets": [
            "bad",
            {"name": "api", "url": "http://api:8000/health"},
            {"url": "missing-name"},
        ]
    }
    r = client.post("/admin/latency-targets", json=body)
    # Should accept 1 cleaned target
    assert r.status_code == 200
    j = r.json()
    assert j.get("count") == 1
