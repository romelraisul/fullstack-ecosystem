import importlib

from backend.app import bridge as bridge_mod


def test_bridge_metric_reuse(monkeypatch):
    # Simulate metrics already existing in registry by adding names to _SEEN then reloading module
    seen = getattr(bridge_mod, "_SEEN", None)
    assert isinstance(seen, set)
    # Add metric names to force reuse path
    for name in [
        "bridge_inputs_total",
        "bridge_experiments_total",
        "bridge_inputs_by_status",
        "bridge_inputs_by_owner",
    ]:
        seen.add(name)
    # Reload module; should not raise even though metrics already exist
    reloaded = importlib.reload(bridge_mod)
    # Access metrics to ensure attributes exist (will be reused or no-op objects)
    assert hasattr(reloaded, "bridge_inputs_total")
    assert hasattr(reloaded, "bridge_inputs_by_status")
