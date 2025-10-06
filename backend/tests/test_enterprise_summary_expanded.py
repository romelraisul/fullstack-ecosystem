from fastapi.testclient import TestClient

from backend.app.main import app

# Attempt to exercise additional by_category aggregation complexity; if tail lines are unreachable
# this test still strengthens distribution coverage.


def test_enterprise_summary_expanded_categories():
    inv = [
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        },
    ]
    # Add many simulated categories to exceed any internal assumptions
    cats = ["ai", "data", "ops", "ml", "sec", "bio", "edge", "cloud"]
    # For every other category, add one simulated ok and one simulated missing api_base (both ok) -> variety
    idx = 0
    for c in cats:
        inv.append({"slug": f"{c}sim{idx}", "category": c, "maturity": "beta"})
        idx += 1
    app.state.systems_inventory = inv
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 32})
    assert r.status_code == 200
    j = r.json()
    ent = j.get("enterprise_summary", {})
    by_cat = ent.get("by_category", {})
    for c in ["quantum"] + cats:
        assert c in by_cat
    # overall_ok_pct should be <=100
    assert 0.0 <= ent.get("overall_ok_pct", 0.0) <= 100.0
