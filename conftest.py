import os
import pathlib
import socket
import sys

import pytest

# Ensure repository root is first on sys.path so that local 'tests' package is importable
# and not shadowed by any third-party distribution named 'tests'. This addresses intermittent
# ModuleNotFoundError: No module named 'tests.test_*' seen during full-suite collection after
# large dependency installation.
_ROOT = pathlib.Path(__file__).resolve().parent
# Insert project root at position 0 to ensure local 'tests' package preference
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Proactively import local tests.utils.metrics to lock module in sys.modules before
# pytest begins discovering other distributions that may define a top-level 'tests'.
try:  # pragma: no cover
    import importlib

    importlib.import_module("tests.utils.metrics")  # noqa: F401
except Exception:
    pass


@pytest.fixture()
def prom_registry():
    if "prom_core" in globals() and prom_core is not None:
        return prom_core.REGISTRY
    return REGISTRY


INTEGRATION_TARGETS = [
    ("localhost", 8010),  # metrics / gateway
    ("localhost", 8444),  # https service
]


def _is_reachable(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@pytest.fixture(autouse=True, scope="session")
def _integration_reachability():
    unavailable = []
    for h, p in INTEGRATION_TARGETS:
        if not _is_reachable(h, p):
            unavailable.append((h, p))
    os.environ["_INTEGRATION_UNAVAILABLE"] = ",".join(f"{h}:{p}" for h, p in unavailable)
    return unavailable


@pytest.fixture(autouse=True)
def _skip_if_integration_unavailable(request):
    if "integration" in request.keywords:
        missing = os.environ.get("_INTEGRATION_UNAVAILABLE", "")
        if missing:
            pytest.skip(f"Skipping integration test (unreachable: {missing})")


# Prometheus duplicate timeseries guard
try:
    import prometheus_client.core as prom_core
    from prometheus_client import REGISTRY, CollectorRegistry
except Exception:  # pragma: no cover
    REGISTRY = None
    CollectorRegistry = None
    prom_core = None


@pytest.fixture(autouse=True)
def _reset_prometheus_registry():
    if CollectorRegistry is None:
        yield
        return
    # Create a fresh registry and monkeypatch the global REGISTRY reference
    try:
        new_registry = CollectorRegistry()
        if prom_core is not None:
            prom_core.REGISTRY = new_registry
        globals()["REGISTRY"] = new_registry
    except Exception:
        pass
    # Run test with fresh registry
    yield
    # Post-test: nothing special; allow GC of registry
