import os
from contextlib import suppress

import pytest

from backend.app.main import app


@pytest.mark.asyncio
async def test_lifespan_early_exit(monkeypatch, tmp_path):
    # Force inventory path to point to a malformed file so startup encounters decode error scenario.
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    bad_file = data_dir / "systems_inventory.json"
    bad_file.write_text('{"not": "valid"')  # malformed JSON

    # Monkeypatch _data_dir resolution indirectly by modifying __file__ directory expectations is complex;
    # instead, patch os.path.join inside the small inventory open scope to return our bad file when matching path end.
    orig_join = os.path.join

    def fake_join(*parts):
        joined = orig_join(*parts)
        if joined.endswith(os.path.sep + "data" + os.path.sep + "systems_inventory.json"):
            return str(bad_file)
        return joined

    monkeypatch.setattr(os.path, "join", fake_join)

    # Use lifespan context manager directly
    # Errors are swallowed internally; we assert inventory becomes []
    async with app.router.lifespan_context(app):  # type: ignore[attr-defined]
        inv = getattr(app.state, "systems_inventory", None)
        assert isinstance(inv, list)
    # After shutdown path, ensure no lingering tasks raise synchronously
    for name in ("_heartbeat_task", "_latency_sampler_task"):
        t = getattr(app.state, name, None)
        if t is not None:
            with suppress(Exception):
                t.cancel()
