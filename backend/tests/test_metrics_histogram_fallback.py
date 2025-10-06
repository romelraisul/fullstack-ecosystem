import pytest

from backend.app import main as main_mod


class BoomHistogram:
    def __init__(self, *a, **k):
        raise RuntimeError("boom histogram")


@pytest.mark.asyncio
async def test_histogram_fallback(monkeypatch):
    # Patch Histogram constructor to force exception path
    monkeypatch.setattr(main_mod, "Histogram", BoomHistogram)
    h = main_mod._safe_histogram("fallback_histogram_test", "Testing fallback", labelnames=["a"])
    # Should return NoOpHistogram-like object with labels().observe() chain not raising
    h.labels(a="x").observe(0.5)
    # Reinvoking should reuse the same no-op instance or existing metric without raising
    h2 = main_mod._safe_histogram("fallback_histogram_test", "Testing fallback", labelnames=["a"])
    h2.labels(a="y").observe(1.0)
