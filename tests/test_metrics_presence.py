import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "autogen" / "ultimate_enterprise_summary.py"
PROM_RULES = ROOT / "docker" / "prometheus_rules.yml"


def test_fleet_error_budget_gauge_declared():
    text = SUMMARY.read_text(encoding="utf-8")
    assert (
        "agent_fleet_error_budget_fraction" in text
    ), "Fleet error budget gauge not declared in summary service"


def test_fleet_error_budget_gauge_used_in_rules():
    if not PROM_RULES.exists():
        return
    rules = PROM_RULES.read_text(encoding="utf-8")
    assert "agent_fleet_error_budget_fraction" in rules, "Gauge not referenced in Prometheus rules"


def test_no_hardcoded_fleet_fraction_constants():
    # Basic heuristic: look for 0.01 usage in rules where gauge should be used
    if not PROM_RULES.exists():
        return
    rules = PROM_RULES.read_text(encoding="utf-8")
    suspicious = re.findall(r"[^0-9]0\.0?1[^0-9]", rules)
    # Allow 0.01 only if accompanied near gauge reference
    if suspicious and "agent_fleet_error_budget_fraction" not in rules:
        raise AssertionError("Found potential hard-coded 0.01 fleet fraction without gauge usage")


def test_burn_rate_formulas_use_dynamic_gauge():
    if not PROM_RULES.exists():
        return
    rules = PROM_RULES.read_text(encoding="utf-8")
    # Look for expressions dividing error burn rate by gauge, e.g. agent:fleet:error_rate_5m / agent_fleet_error_budget_fraction
    burn_exprs = re.findall(
        r"agent:fleet:error_rate_[0-9a-z]+\s*/\s*agent_fleet_error_budget_fraction", rules
    )
    assert burn_exprs, "No burn-rate formulas found using dynamic gauge denominator"


def test_expected_multiplier_constants_present():
    """Assert that key burn/threshold multipliers appear in rule expressions.

    Multipliers:
      - 14x : fast burn (5m/1h, fleet & per-agent)
      - 6x  : slow burn (30m/6h)
      - 3x  : fleet high error rate threshold (3 * budget)
      - 2x  : acceleration (5m > 2x 30m baseline) & medium threshold tier
      - 5x  : critical per-agent error rate (>=5x budget)
    """
    if not PROM_RULES.exists():
        return
    text = PROM_RULES.read_text(encoding="utf-8")
    expected = {
        "14": r">\s*14",
        "6": r">\s*6",
        "3": r">\s*3\s*\*\s*agent_fleet_error_budget_fraction",  # ensure 3 * gauge present
        "2": r">\s*2\s*\*",  # acceleration or threshold tier using 2 *
        "5": r">\s*5\s*\*",  # critical 5x tier
    }
    missing = []
    for label, pattern in expected.items():
        if not re.search(pattern, text):
            missing.append(label)
    if missing:
        raise AssertionError(f"Missing expected multiplier patterns: {', '.join(missing)}")
