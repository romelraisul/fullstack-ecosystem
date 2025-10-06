import pytest

from backend.app import main as main_mod


class FakeRegistry:
    def __init__(self, collectors=None):
        self._names_to_collectors = collectors or {}


class ExplodingCounter:
    def __init__(self, *a, **k):
        raise RuntimeError("counter boom")


@pytest.mark.asyncio
async def test_metrics_existing_mismatch(monkeypatch):
    # Patch global prometheus_core.REGISTRY to a fake one missing metric names so _existing_metric returns None
    fake = FakeRegistry({})
    if hasattr(main_mod, "_prom_core"):
        monkeypatch.setattr(main_mod._prom_core, "REGISTRY", fake, raising=True)
    # Patch Counter to raise forcing fallback to existing lookup (which yields None) then NoOp path
    monkeypatch.setattr(main_mod, "Counter", ExplodingCounter)

    c = main_mod._safe_counter("fallback_counter_test", "Fallback counter")
    # NoOpCounter emulation: labels().inc() must not raise
    c.labels(test="x").inc()
    # Re-call to ensure reuse returns same style object
    c2 = main_mod._safe_counter("fallback_counter_test", "Fallback counter again")
    c2.labels(test="y").inc()
