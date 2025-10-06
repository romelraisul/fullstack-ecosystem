import httpx
from fastapi.testclient import TestClient

from backend.app.main import app

# We'll construct a synthetic inventory large enough to exceed sample slice (5)
# and mix categories with ok/error outcomes.


class MixedHTTPClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *args, **kwargs):
        # Simulate behavior for candidate endpoints resolution.
        # We'll force half of the slugs to succeed on first candidate (health) and half to fail all.
        # Extract slug heuristically from url path tail if present.
        # For quantum slugs we don't want to interfere here; those are handled separately in other tests.
        raise httpx.ConnectError(
            "forced generic http unreachable", request=httpx.Request("GET", url)
        )


# We only manipulate generic HTTP behavior by ensuring they appear as simulated when api_base empty
# and injecting a mixture of simulated ok and a few explicit API bases to trigger generic HTTP attempts.


def build_inventory():
    inv = []
    # 1 quantum slug to ensure quantum fields present
    inv.append(
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        }
    )
    # Add 9 additional systems across 3 categories (ai, data, ops) so total > 5 sample slice
    # First 3: simulated (no api_base) => ok fast
    for i in range(3):
        inv.append({"slug": f"aisim{i}", "category": "ai", "maturity": "beta"})
    # Next 3: with api_base so generic HTTP tries & we patch client to fail (errors)
    for i in range(3):
        inv.append(
            {
                "slug": f"datahttp{i}",
                "api_base": f"http://fake{i}",
                "category": "data",
                "maturity": "beta",
            }
        )
    # Final 2: simulated again (ok) different category
    for i in range(2):
        inv.append({"slug": f"opsim{i}", "category": "ops", "maturity": "alpha"})
    return inv


def test_enterprise_summary_tail(monkeypatch):
    # Inject inventory
    app.state.systems_inventory = build_inventory()

    # Patch AsyncClient so generic HTTP (with api_base) always fails candidates causing error paths
    monkeypatch.setattr(httpx, "AsyncClient", MixedHTTPClient)

    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r.status_code == 200
    j = r.json()
    ent = j.get("enterprise_summary")
    assert ent and "by_category" in ent
    by_cat = ent["by_category"]
    # Expect categories quantum, ai, data, ops present
    for cat in ["quantum", "ai", "data", "ops"]:
        assert cat in by_cat, f"missing category {cat} in {by_cat}"
    # ai total 3 ok all
    assert by_cat["ai"]["total"] == 3 and by_cat["ai"]["ok"] == 3
    # data total 3 all errors
    assert by_cat["data"]["total"] == 3 and by_cat["data"]["errors"] == 3
    # ops total 2 ok
    assert by_cat["ops"]["total"] == 2
    # sample limited to 5
    sample = j.get("sample")
    assert isinstance(sample, list) and len(sample) <= 5
    # overall_ok_pct within 0-100 and float
    assert isinstance(ent["overall_ok_pct"], (int, float)) and 0.0 <= ent["overall_ok_pct"] <= 100.0
