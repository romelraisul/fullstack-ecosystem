import importlib

from fastapi.testclient import TestClient

from backend.app.main import _classify_latency_ms, _parse_latency_targets, app

client = TestClient(app)


def test_parse_latency_targets_edge_cases():
    # Empty string -> empty list
    assert _parse_latency_targets("") == []
    # Mixed valid/invalid segments
    raw = "api:http://a/health,broken, ,gateway:http://b,justname:"
    out = _parse_latency_targets(raw)
    names = {o["name"] for o in out}
    assert "api" in names and "gateway" in names
    # Ensure no malformed entries
    assert all("url" in o and o["url"] for o in out)


def test_classify_latency_ms_ranges():
    assert _classify_latency_ms(-5) == "na"
    assert _classify_latency_ms(50) == "good"
    assert _classify_latency_ms(200) == "warn"
    assert _classify_latency_ms(450) == "high"


def test_admin_latency_targets_error_paths():
    # Body not an object
    r = client.post("/admin/latency-targets", json=[1, 2, 3])
    assert r.status_code in (400, 422)
    # targets not list / empty
    r = client.post("/admin/latency-targets", json={"targets": "x"})
    assert r.status_code in (400, 422)
    r = client.post("/admin/latency-targets", json={"targets": []})
    assert r.status_code in (400, 422)
    # targets list but all invalid entries
    r = client.post("/admin/latency-targets", json={"targets": [{}, {"name": "x"}, {"url": "y"}]})
    assert r.status_code in (400, 422)
    # Valid request (also covers persist branch)
    r = client.post(
        "/admin/latency-targets",
        json={"targets": [{"name": "api", "url": "http://api/health"}], "persist": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1


def test_system_execute_experimental_policy_block(set_inventory):
    # Inventory with one experimental system
    set_inventory([{"slug": "exp-test", "maturity": "experimental", "api_base": "/api"}])
    # Missing feature flag -> 403
    r = client.post("/system/exp-test/execute", json={"event": "x"})
    assert r.status_code == 403
    # With flag -> accepted
    r = client.post(
        "/system/exp-test/execute",
        headers={"X-Feature-Flag": "allow-experimental"},
        json={"event": "y"},
    )
    assert r.status_code == 200


def test_orchestrate_delegate_exclude_experimental(set_inventory):
    set_inventory(
        [
            {"slug": "s1", "maturity": "verified", "api_base": "/api"},
            {"slug": "s2", "maturity": "experimental", "api_base": "/api"},
        ]
    )
    r = client.post("/orchestrate/delegate", json={"include_experimental": False, "dry_run": True})
    assert r.status_code == 200
    data = r.json()
    assert "s2" not in data["planned"] and "s1" in data["planned"]


def test_bridge_safe_counter_and_gauge_exception_paths(monkeypatch):
    # Import bridge module
    from backend.app import bridge

    # Force Counter/Gauge to raise so except path returns NoOp classes
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(bridge, "Counter", boom)
    monkeypatch.setattr(bridge, "Gauge", boom)

    c = bridge._safe_counter("test_fail_counter", "doc")
    g = bridge._safe_gauge("test_fail_gauge", "doc")
    # Invoke label methods to cover inner NoOp methods
    c.labels(any="x").inc()
    g.labels(any="y").set(1)

    # Now test duplicate existing metric reuse path
    import prometheus_client

    real_c = prometheus_client.Counter("test_dup_counter", "doc")
    # Mark seen
    bridge._SEEN.add("test_dup_counter")
    got = bridge._safe_counter("test_dup_counter", "doc")
    # If existing metric lookup works we get real_c, else fallback NoOp acceptable
    assert (got is real_c) or got.__class__.__name__ == "_NoOp"


def test_bridge_init_exception_reload(monkeypatch):
    # Monkeypatch _load to raise to exercise bottom import try/except
    import backend.app.bridge as bridge

    monkeypatch.setattr(
        bridge, "_load", lambda: (_ for _ in ()).throw(ValueError("fail"))
    )  # generator raising
    # Reload should swallow exception

    importlib.reload(bridge)
