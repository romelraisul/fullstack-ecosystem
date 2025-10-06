import pytest
import httpx
from backend.app.main import app

# Autouse fixture to neutralize rate limiting side-effects across tests
@pytest.fixture(autouse=True)
def _relax_rate_limits(monkeypatch):
    # If RateLimitMiddleware stored counters or rate values on app, adjust them; fallback: add attribute flag consumed by middleware if it checks.
    # We don't import middleware directly (avoid dependency churn); just set a high sentinel attribute the middleware can optionally consult.
    setattr(app.state, 'TEST_RATE_LIMIT_BYPASS', True)
    yield
    # Cleanup not strictly necessary; leaving the flag is fine between tests.

@pytest.fixture
def set_inventory():
    def _setter(items):
        app.state.systems_inventory = items
    return _setter

class QuantumSuccessClient:
    def __init__(self, *args, **kwargs):
        # Accept arbitrary constructor arguments to mirror httpx.AsyncClient signature in tests
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def get(self, url, params=None, headers=None):
        if url.endswith('/health'):
            return type('Resp', (), {'status_code': 200, 'json': lambda self=None: {'status': 'ok'}, 'raise_for_status': lambda self=None: None, 'headers': {'content-type': 'application/json'}})()
        if '/api/quantum/bell' in url:
            return type('Resp', (), {'status_code': 200, 'json': lambda self=None: {'counts': {'00': 10, '11': 9}}, 'raise_for_status': lambda self=None: None, 'headers': {'content-type': 'application/json'}})()
        if '/api/quantum/ghz' in url:
            return type('Resp', (), {'status_code': 200, 'json': lambda self=None: {'counts': {'000': 5, '111': 4}}, 'raise_for_status': lambda self=None: None, 'headers': {'content-type': 'application/json'}})()
        return type('Resp', (), {'status_code': 200, 'json': lambda self=None: {}, 'raise_for_status': lambda self=None: None, 'headers': {'content-type': 'application/json'}})()

@pytest.fixture
def mock_quantum_success(monkeypatch):
    monkeypatch.setattr(httpx, 'AsyncClient', QuantumSuccessClient)
    return QuantumSuccessClient

class QuantumHealthFailClient(QuantumSuccessClient):
    async def get(self, url, params=None, headers=None):
        if url.endswith('/health'):
            raise RuntimeError('health fail')
        return await super().get(url, params=params, headers=headers)

class QuantumBellFailClient(QuantumSuccessClient):
    async def get(self, url, params=None, headers=None):
        if '/api/quantum/bell' in url:
            raise RuntimeError('bell fail')
        return await super().get(url, params=params, headers=headers)

class QuantumGHZFailClient(QuantumSuccessClient):
    async def get(self, url, params=None, headers=None):
        if '/api/quantum/ghz' in url:
            raise RuntimeError('ghz fail')
        return await super().get(url, params=params, headers=headers)

@pytest.fixture
def mock_quantum_health_fail(monkeypatch):
    monkeypatch.setattr(httpx, 'AsyncClient', QuantumHealthFailClient)
    return QuantumHealthFailClient

@pytest.fixture
def mock_quantum_bell_fail(monkeypatch):
    monkeypatch.setattr(httpx, 'AsyncClient', QuantumBellFailClient)
    return QuantumBellFailClient

@pytest.fixture
def mock_quantum_ghz_fail(monkeypatch):
    monkeypatch.setattr(httpx, 'AsyncClient', QuantumGHZFailClient)
    return QuantumGHZFailClient

class QuantumPostProcessFailClient(QuantumSuccessClient):
    async def get(self, url, params=None, headers=None):
        # Same as success for health, bell, ghz; after ghz we raise on an artificial follow-up path
        if '/api/quantum/ghz' in url:
            # Return success first then trigger side-effect error by raising on a dummy subsequent call
            return type('Resp', (), {'status_code': 200, 'json': lambda self=None: {'counts': {'000': 6, '111': 5}, 'trigger_error': True}, 'raise_for_status': lambda self=None: None, 'headers': {'content-type': 'application/json'}})()
        return await super().get(url, params=params, headers=headers)

@pytest.fixture
def mock_quantum_postprocess_fail(monkeypatch):
    monkeypatch.setattr(httpx, 'AsyncClient', QuantumPostProcessFailClient)
    return QuantumPostProcessFailClient

git branch -M main
git push -u origin main

Select-String -Path .github/workflows/container-security-lite.yml "`t"
