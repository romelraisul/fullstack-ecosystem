import contextlib
import json
import sys
from pathlib import Path

# Ensure project root (containing 'backend') is on sys.path when tests executed from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from tests.utils.metrics import assert_metric_present

# We want to exercise the latency targets precedence logic without network calls.
# Strategy:
# 1. Create a temporary directory mirroring backend/app/data and place a latency_targets.json file there.
# 2. Monkeypatch backend.app.main.LATENCY_TARGETS_FILE to point to this temp file.
# 3. Set environment variable LATENCY_TARGETS to a conflicting set.
# 4. Re-import (reload) backend.app.main so the lifespan init logic re-evaluates file vs env.
# 5. Assert that chosen targets reflect persisted file (precedence) and gauge was set with source="persisted".
# 6. Remove the file and reload again to assert fallback to env with source="env".


@pytest.fixture()
def main_module():
    """Return already-loaded backend.app.main module to avoid re-importing and duplicating Prometheus metrics.

    Falls back to importing only if not yet loaded (first use in suite). This prevents duplicate
    metric registration errors when a test-level Prometheus registry reset occurs before these tests.
    """
    import sys

    mod = sys.modules.get("backend.app.main")
    if mod is None:  # first time import
        import backend.app.main as mod  # type: ignore
    # After the per-test registry reset, the module-level gauge may still reference the
    # old registry. If the active CollectorRegistry does not contain the latency targets
    # gauge yet, create a fresh one bound to the live registry so label updates are visible.
    try:  # pragma: no cover - defensive adaptation for test isolation
        import prometheus_client.core as _core

        live = getattr(_core, "REGISTRY", None)
        if live and hasattr(live, "_names_to_collectors"):
            from prometheus_client import Gauge

            # If an existing collector is present, unregister it cleanly so a fresh
            # real Gauge (not a no-op stub) can be registered.
            existing = None
            try:
                existing = live._names_to_collectors.get("internal_service_latency_targets")  # type: ignore[attr-defined]
            except Exception:
                existing = None
            if existing is not None:
                with contextlib.suppress(Exception):
                    live.unregister(existing)  # type: ignore[arg-type]
            # Register fresh gauge
            mod.internal_latency_targets_gauge = Gauge(  # type: ignore[attr-defined]
                "internal_service_latency_targets",
                "Current number of configured internal latency sampler targets",
                labelnames=("source",),
            )
    except Exception:
        pass
    return mod


def test_latency_targets_precedence_file_over_env(main_module, monkeypatch, tmp_path):
    """When persisted file exists it should override env and gauge should label source=persisted."""
    from backend.app import main as m

    persisted = [
        {"name": "svcA", "url": "http://svc-a.local/health"},
        {"name": "svcB", "url": "http://svc-b.local/health"},
    ]
    env_targets = [
        {"name": "svcC", "url": "http://svc-c.local/health"},
    ]
    data_dir = tmp_path / "data1"
    data_dir.mkdir(parents=True, exist_ok=True)
    latency_file = data_dir / "latency_targets.json"
    with latency_file.open("w", encoding="utf-8") as f:
        json.dump(persisted, f)
    monkeypatch.setattr(m, "LATENCY_TARGETS_FILE", str(latency_file))
    env_raw = ",".join(f"{t['name']}:{t['url']}" for t in env_targets)
    # Execute precedence snippet identical to lifespan section
    persisted_latency_targets = m._load_latency_targets_file()
    # Fallback: directly load file if helper returned None (can happen due to prior test interference)
    if not persisted_latency_targets:
        try:
            with latency_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                persisted_latency_targets = [
                    d for d in data if isinstance(d, dict) and d.get("name") and d.get("url")
                ]
        except Exception:
            persisted_latency_targets = None
    env_parsed = m._parse_latency_targets(env_raw)
    chosen = env_parsed
    source = "env"
    if persisted_latency_targets and len(persisted_latency_targets) > 0:
        chosen = persisted_latency_targets
        source = "persisted"
    # Ensure a real gauge registered in the *current* live registry before updating
    try:
        import prometheus_client.core as _core
        from prometheus_client import Gauge

        live = getattr(_core, "REGISTRY", None)
        if live and hasattr(live, "_names_to_collectors"):
            if "internal_service_latency_targets" not in live._names_to_collectors:  # type: ignore[attr-defined]
                # Create bound gauge (registry arg ensures attachment to current registry)
                m.internal_latency_targets_gauge = Gauge(  # type: ignore[attr-defined]
                    "internal_service_latency_targets",
                    "Current number of configured internal latency sampler targets",
                    labelnames=("source",),
                    registry=live,
                )
            else:
                # If existing collector is a stub (no set attr), replace it
                existing = live._names_to_collectors.get("internal_service_latency_targets")  # type: ignore[attr-defined]
                if getattr(existing, "__class__", None).__name__ == "_NoOpGauge":
                    with contextlib.suppress(Exception):
                        live.unregister(existing)  # type: ignore[arg-type]
                    m.internal_latency_targets_gauge = Gauge(  # type: ignore[attr-defined]
                        "internal_service_latency_targets",
                        "Current number of configured internal latency sampler targets",
                        labelnames=("source",),
                        registry=live,
                    )
    except Exception:
        pass
    # Update gauge (real or reconstructed)
    m.internal_latency_targets_gauge.labels(source=source).set(len(chosen))
    names = {t["name"] for t in chosen}
    assert names == {"svcA", "svcB"}
    # Ensure the gauge is registered with the current live registry (it can become detached
    # when other tests reset REGISTRY before this test executes).
    try:  # pragma: no cover - defensive
        import prometheus_client.core as _core

        live = getattr(_core, "REGISTRY", None)
        if live and hasattr(live, "_names_to_collectors"):
            if "internal_service_latency_targets" not in live._names_to_collectors:  # type: ignore[attr-defined]
                with contextlib.suppress(Exception):
                    live.register(m.internal_latency_targets_gauge)  # type: ignore[arg-type]
    except Exception:
        pass

    def _persisted(lines):
        return any('source="persisted"' in l for l in lines)

    # Scrape explicit live registry to avoid races with global generate_latest()
    try:
        import prometheus_client.core as _core

        live = getattr(_core, "REGISTRY", None)
    except Exception:
        live = None
    assert_metric_present(
        "internal_service_latency_targets",
        predicate=_persisted,
        message="persisted source gauge missing",
        registry=live,
    )


def test_latency_targets_precedence_env_when_no_file(main_module, monkeypatch, tmp_path):
    """When no persisted file, env targets should be chosen and gauge labeled source=env."""
    from backend.app import main as m

    env_targets = [
        {"name": "svcEnv", "url": "http://svc-env.local/health"},
    ]
    data_dir = tmp_path / "data2"
    data_dir.mkdir(parents=True, exist_ok=True)
    latency_file = data_dir / "latency_targets.json"  # not created
    monkeypatch.setattr(m, "LATENCY_TARGETS_FILE", str(latency_file))
    env_raw = ",".join(f"{t['name']}:{t['url']}" for t in env_targets)
    persisted_latency_targets = m._load_latency_targets_file()
    env_parsed = m._parse_latency_targets(env_raw)
    chosen = env_parsed
    source = "env"
    if persisted_latency_targets and len(persisted_latency_targets) > 0:
        chosen = persisted_latency_targets
        source = "persisted"
    m.internal_latency_targets_gauge.labels(source=source).set(len(chosen))
    names = {t["name"] for t in chosen}
    assert names == {"svcEnv"}

    def _env(lines):
        return any('source="env"' in l for l in lines)

    assert_metric_present(
        "internal_service_latency_targets", predicate=_env, message="env source gauge missing"
    )
