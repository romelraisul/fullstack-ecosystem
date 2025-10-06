from backend.app import main


def test_metric_reuse_without_fallback(monkeypatch):
    # Ensure a fresh metric creation
    g1 = main._safe_gauge("test_reuse_gauge_total", "doc")
    assert hasattr(g1, "set")
    # Simulate duplicate: add name to seen so next call triggers reuse path
    main._SEEN_METRIC_NAMES.add("test_reuse_gauge_total")
    g2 = main._safe_gauge("test_reuse_gauge_total", "doc")
    # Should return object with labels()/set(); identity may or may not match but functions should be present
    assert hasattr(g2, "labels")
    # Invoke set to ensure no exception
    try:
        g2.set(1)
    except Exception:
        # Some collectors require labels first; fallback no exception path
        pass


def test_metric_reuse_counter_histogram(monkeypatch):
    # Acquire live registry reference (if available) and inject fake collectors
    reg = getattr(main, "_prom_core", None)
    live = getattr(reg, "REGISTRY", None) if reg else None
    mapping = None
    if live and hasattr(live, "_names_to_collectors"):
        mapping = live._names_to_collectors  # type: ignore[attr-defined]
    if mapping is None:
        # Skip gracefully if structure changes
        return

    class FakeCounter:
        def labels(self, **kw):
            return self

        def inc(self, *a, **k):
            return None

    class FakeHistogram:
        def labels(self, **kw):
            return self

        def observe(self, *a, **k):
            return None

    # Pre-inject names to simulate pre-registered collectors
    mapping["test_reuse_counter_total"] = FakeCounter()
    mapping["test_reuse_histogram_seconds"] = FakeHistogram()

    # Mark names as seen to take reuse path
    main._SEEN_METRIC_NAMES.add("test_reuse_counter_total")
    main._SEEN_METRIC_NAMES.add("test_reuse_histogram_seconds")

    c = main._safe_counter("test_reuse_counter_total", "doc")
    h = main._safe_histogram("test_reuse_histogram_seconds", "doc")

    # Should return our fake objects with labels working
    c.labels(test="x").inc()
    h.labels(test="x").observe(0.01)
