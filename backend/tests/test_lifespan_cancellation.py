import asyncio

from fastapi.testclient import TestClient

from backend.app.main import app

# We will trigger early cancellation by cancelling tasks after first request.


def test_lifespan_early_cancellation():
    with TestClient(app):
        # Issue a trivial request (metrics absent maybe) - root not defined; use /metrics if available else skip
        # We just want to ensure app started; then cancel tasks.
        hb = getattr(app.state, "_heartbeat_task", None)
        lt = getattr(app.state, "_latency_sampler_task", None)
        # Cancel if present
        for t in [hb, lt]:
            if t and not t.done():
                t.cancel()
        # Force a short sleep to allow cancellation branch to execute before context exit
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
    # Exiting context should await cancelled tasks via suppression blocks (lines around 265,292)
