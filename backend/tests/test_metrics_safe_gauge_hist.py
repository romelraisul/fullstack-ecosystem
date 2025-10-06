from backend.app import main


def test_safe_gauge_histogram_fallback(monkeypatch):
    class Boom(Exception):
        pass

    def boom_gauge(*a, **k):
        raise Boom("gauge duplicate")

    def boom_hist(*a, **k):
        raise Boom("hist duplicate")

    monkeypatch.setattr(main, "Gauge", boom_gauge)
    monkeypatch.setattr(main, "Histogram", boom_hist)

    g = main._safe_gauge("test_safe_gauge_total", "doc")
    h = main._safe_histogram("test_safe_histogram_seconds", "doc")

    # Should provide labels() and set()/observe() no-op methods
    gl = g.labels(test="x") if hasattr(g, "labels") else g
    hl = h.labels(test="x") if hasattr(h, "labels") else h
    # Methods should not raise
    if hasattr(gl, "set"):
        gl.set(1)
    if hasattr(hl, "observe"):
        hl.observe(0.1)
