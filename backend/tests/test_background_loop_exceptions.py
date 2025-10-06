import asyncio

import httpx
from fastapi.testclient import TestClient

from backend.app import main


class FailingAsyncClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):  # always raise to exercise latency sampler exception swallow
        raise RuntimeError("sampler failure")


async def _tick():
    await asyncio.sleep(0.05)


def test_background_loops_exception_swallow(monkeypatch):
    # Patch httpx AsyncClient used by latency sampler
    monkeypatch.setattr(httpx, "AsyncClient", FailingAsyncClient)

    # Patch _record_event to raise in heartbeat
    def boom(event, slug, extra=None):
        raise RuntimeError("event failure")

    monkeypatch.setattr(main, "_record_event", boom)
    # Spin up app; loops will attempt work and raise internally
    with TestClient(main.app) as client:
        # Allow a tiny sleep so background tasks run at least once
        asyncio.get_event_loop().run_until_complete(_tick())
        # Service must remain healthy
        r = client.get("/health")
        assert r.status_code == 200
