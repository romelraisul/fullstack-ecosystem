import pytest

from backend.app import main as main_mod


@pytest.mark.asyncio
async def test_event_ring_capacity_and_persist(monkeypatch, tmp_path):
    # Redirect persistence path to temp file
    persist_file = tmp_path / "events_recent.json"

    def fake_events_persist_path():
        return str(persist_file)

    monkeypatch.setattr(main_mod, "_events_persist_path", fake_events_persist_path)

    calls = {}
    orig_persist = main_mod._persist_events_ring

    def tracking_persist():
        calls["count"] = calls.get("count", 0) + 1
        return orig_persist()

    monkeypatch.setattr(main_mod, "_persist_events_ring", tracking_persist)

    # Flood events beyond ring max
    main_mod._EVENTS_RING.clear()
    for i in range(main_mod._EVENTS_RING_MAX + 25):
        main_mod._record_event("system.execute.ok", f"slug-{i % 5}", {"i": i})

    # Ensure trimming occurred (length == max)
    assert len(main_mod._EVENTS_RING) == main_mod._EVENTS_RING_MAX
    # Persistence should have been called many times
    assert calls.get("count", 0) >= main_mod._EVENTS_RING_MAX // 4  # heuristic lower bound
    # File should exist with <= max events
    assert persist_file.exists()
    import json

    data = json.loads(persist_file.read_text("utf-8"))
    assert isinstance(data, list)
    assert len(data) <= main_mod._EVENTS_RING_MAX
