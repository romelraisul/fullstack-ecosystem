import prometheus_client.core as core

from backend.app import main as m

# We'll exercise reuse + exception fallback behavior for _safe_counter and _safe_histogram.


class FakeCollector:
    def __init__(self, name):
        self._name = name

    def labels(self, **kw):
        return self

    def inc(self, *a, **k):
        return None

    def observe(self, *a, **k):
        return None


def test_safe_counter_reuse(monkeypatch):
    name = "test_reuse_counter"
    # Pretend name already seen
    m._SEEN_METRIC_NAMES.add(name)
    reg = core.REGISTRY
    # Inject fake collector in live registry mapping
    reg._names_to_collectors[name] = FakeCollector(name)  # type: ignore[attr-defined]
    c = m._safe_counter(name, "doc", registry=reg)
    assert isinstance(c, FakeCollector)


def test_safe_histogram_exception_fallback(monkeypatch):
    name = "test_histogram_fail"
    # Force constructor to raise
    original = m.Histogram

    class Boom(Exception):
        pass

    def raising_hist(*a, **k):
        raise Boom("fail")

    monkeypatch.setattr(m, "Histogram", raising_hist)
    # Not seen yet; attempt will raise -> fallback path -> existing_metric returns None -> stub class
    h = m._safe_histogram(name, "doc")
    assert h.__class__.__name__ in {"_NoOpHistogram"}
    # Now make existing metric present and ensure reuse next time
    reg = core.REGISTRY
    fake = FakeCollector(name)
    reg._names_to_collectors[name] = fake  # type: ignore[attr-defined]
    # Mark as seen
    m._SEEN_METRIC_NAMES.add(name)
    # Second call should return fake (reuse branch)
    h2 = m._safe_histogram(name, "doc")
    assert h2 is fake
    # restore
    monkeypatch.setattr(m, "Histogram", original)
