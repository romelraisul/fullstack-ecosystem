import builtins
import importlib
import json

# Module under test
MODULE_PATH = "scripts.synthetic_seed"

REGISTRY_FIXTURE = [
    {"name": "alpha"},
    {"name": "beta"},
]


def write_registry(tmp_path):
    p = tmp_path / "agent_registry.json"
    p.write_text(json.dumps(REGISTRY_FIXTURE), encoding="utf-8")
    return p


def test_seeder_fallback_without_prometheus(monkeypatch, tmp_path):
    """If Prometheus query fails (returns None), all agents below threshold (treated as 0 rps) can be selected.

    We force DRY_RUN so no network calls are made, and patch httpx to raise ImportError logic (simulate missing).
    """
    reg = write_registry(tmp_path)

    # Ensure environment variables direct module to our temp registry & dry-run mode
    monkeypatch.setenv("AGENT_REGISTRY", str(reg))
    monkeypatch.setenv("SEED_DRY_RUN", "1")
    monkeypatch.setenv("SEED_RPS_THRESHOLD", "0.1")
    monkeypatch.setenv("SEED_MAX_AGENTS", "5")

    # Remove httpx to force prom query fallback path
    if "httpx" in globals():
        del globals()["httpx"]
    if "httpx" in MODULE_PATH:
        pass

    # Import module fresh
    if MODULE_PATH in list(importlib.sys.modules):
        del importlib.sys.modules[MODULE_PATH]
    mod = importlib.import_module(MODULE_PATH)

    # Patch prom_instant_query to return None explicitly
    def _none_query(_):
        return None

    monkeypatch.setattr(mod, "prom_instant_query", _none_query)

    # Capture printed output
    lines = []

    def fake_print(*a, **k):
        lines.append(" ".join(str(x) for x in a))

    monkeypatch.setattr(builtins, "print", fake_print)

    exit_code = mod.main()
    assert exit_code == 0
    # Expect selection message listing agents (both alpha and beta should appear)
    joined = "\n".join(lines)
    assert "Selected 2 agents" in joined
    assert "alpha" in joined and "beta" in joined
