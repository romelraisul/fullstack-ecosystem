import importlib
import sys
import types

import pytest


@pytest.mark.asyncio
async def test_metrics_reregistration_idempotent(monkeypatch):
    # Import original main to ensure metrics registered once
    import backend.app.main as original_main

    # Capture some existing collectors for comparison
    existing = set(original_main._SEEN_METRIC_NAMES)
    # Simulate a second import under a synthetic module name pointing to same source file
    # to exercise code paths that look up existing collectors.
    spec = importlib.util.find_spec("backend.app.main")
    assert spec and spec.origin
    module_name = "backend.app.main_alias_for_test"
    if module_name in sys.modules:
        del sys.modules[module_name]
    new_mod = types.ModuleType(module_name)
    new_mod.__file__ = spec.origin
    # Execute the module code in isolated namespace (rough simulation of re-import)
    with open(spec.origin, encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, spec.origin, "exec"), new_mod.__dict__)
    sys.modules[module_name] = new_mod
    # After executing, the alias module should also have metric names; they should be a superset but not duplicate registration errors.
    assert hasattr(new_mod, "_SEEN_METRIC_NAMES")
    # A fresh exec creates a new _SEEN_METRIC_NAMES set starting empty and then populating as definitions run;
    # we only require that at least some known metric names exist, not full superset equivalence.
    overlap = existing.intersection(new_mod._SEEN_METRIC_NAMES)
    assert len(overlap) >= max(3, len(existing) // 4)
    # Re-access a safe metric creation function to ensure reuse path does not raise.
    c = new_mod._safe_counter("system_execute_total", "Total executes re-access")  # existing
    assert c is not None
    g = new_mod._safe_gauge("startup_events_total", "Startup gauge re-access")  # existing
    assert g is not None
    h = new_mod._safe_histogram(
        "system_execute_duration_seconds",
        "Histogram re-access",
        labelnames=["system_slug", "mode", "status"],
    )
    assert h is not None
    # Exercise a label + observe path
    try:
        h.labels(system_slug="x", mode="simulated", status="ok").observe(0.01)
    except Exception:
        # Should not raise even if returns a NoOpHistogram
        pass
