# Adding a New Project / Subsystem

This repository aggregates many domain / capability subsystems (e.g. *alpha_mega_system_framework*,
*adjacent_markets_command_center*, etc.). To add a new project with consistent governance, follow this
lightweight checklist.

## 1. Naming & Files

- Choose a concise, snake_case module name (e.g. `supply_chain_optimizer`).
- Add a primary Python file `supply_chain_optimizer.py` at repo root (mirrors existing pattern) or create a
  package directory if multi-file.
- If it owns persistent state, create a companion SQLite DB file named `<name>.db` (if using the simple local
  persistence approach seen in other modules).
- Optional: Add a short markdown concept doc under `docs/projects/<name>.md`.

## 2. Minimal Module Skeleton

```python
"""Supply Chain Optimizer subsystem.
Purpose: High-level description.
"""
from __future__ import annotations

__all__ = ["optimize", "version"]

version = "0.1.0"

class SupplyChainOptimizer:
    def optimize(self, graph):
        # TODO: implement
        return {"status": "placeholder"}

def optimize(graph):
    return SupplyChainOptimizer().optimize(graph)
```

## 3. Inventory Registration (for Orchestration)

If the subsystem should appear in orchestrator views or be targeted by delegate/experiment endpoints:

1. Open `backend/app/data/systems_inventory.json`.
2. Add an entry:

```json
{
  "slug": "supply-chain-optimizer",
  "category": "optimization",
  "maturity": "experimental",
  "owner": "platform",
  "api_base": "/api"  // or omit if not exposing direct routes
}
```

1. POST `/admin/reload-inventory` (if API running) to pick up changes.

## 4. Event Taxonomy (Optional)

If it emits custom events, consider adding them to `backend/app/data/events_registry.json`:

```json
{"events": [
  {"name": "supply.optimizer.run", "description": "Optimization execution completed"}
]}
```

## 5. Governance & Stability Hooks

- If it exposes API endpoints, ensure they are part of the generated OpenAPI (FastAPI router or automatic
  discovery) so stability metrics & diff analysis naturally include them.
- Avoid publishing unstable (breaking) routes without version guard; leverage semantic version guidance if
  external consumers rely on it.

## 6. Tests

Add at least one smoke test under `tests/` referencing the new module. Example:

```python
def test_supply_chain_optimizer_placeholder():
    from supply_chain_optimizer import optimize
    out = optimize({})
    assert out["status"] == "placeholder"
```

## 7. Metrics / Telemetry (Optional)

If you need Prometheus metrics, follow existing patterns using `_safe_counter` / `_safe_gauge` utilities in
`backend/app/main.py` to avoid duplicate registration in tests.

## 8. Database (Optional)

If adding a `<name>.db` file:

- Prefer generating it lazily on first write; don't commit large seeded data unless necessary.
- Document schema briefly in a `docs/projects/<name>.md` appendix.

## 9. Roadmap / README Reference

Add a short bullet to the main `README.md` under a suitable section (e.g. *Subsystem Inventory*) describing the
purpose / maturity.

## 10. Versioning

Track an internal `version` variable (as shown) so future semantic alignment can reason about module-level
evolution if exported via API.

---
**Fast Path Recap**: (1) module file; (2) inventory entry; (3) optional events; (4) smoke test; (5) README bullet.

Future automation could enforce presence of these via a validation script (e.g. `scripts/validate_subsystems.py`).
