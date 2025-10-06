from backend.app import main


def test_safe_counter_duplicate_registration(monkeypatch):
    # Force _existing_metric to return None and simulate a failure in Counter creation
    class Boom(Exception):
        pass

    class FakeCounter:
        def __init__(*a, **k):
            raise Boom("duplicate")

    # Patch Counter symbol used in main by injecting failure
    monkeypatch.setattr(main, "Counter", FakeCounter)
    # Ensure metric name tracked as seen to trigger fallback path
    name = "test_duplicate_metric_total"
    main._SEEN_METRIC_NAMES.add(name)
    m = main._safe_counter(name, "doc")
    # Should return object with labels() and inc() even after exception
    assert hasattr(m, "labels")
    lbl = m.labels(test="x")
    assert hasattr(lbl, "inc")
