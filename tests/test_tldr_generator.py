import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_runbook_tldr.py"
OPS = ROOT / "OPERATIONS.md"
SRC = ROOT / "docs" / "runbook_sources.yml"


def test_script_exists():
    assert SCRIPT.exists(), "TLDR generator script missing"


def test_section_order_matches_sources():
    # Import the script as a module to access build_tldr
    spec = importlib.util.spec_from_file_location("tldr_gen", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    data = mod.load_sources()
    rendered = mod.build_tldr(data)
    # Ensure first expected heading order sequence appears
    expected = [
        "## Runbook TL;DR",
        "### Core Commands",
        "### Key Files",
        "### Add an Agent",
        "### Dynamic SLO Thresholds",
        "### Synthetic Traffic",
        "### Security & Tracing",
        "### Troubleshooting Fast Path",
        "### Escalation Criteria",
    ]
    # All headings present
    for h in expected:
        assert h in rendered, f"Missing heading {h}"
    # Order check: index must be increasing
    indices = [rendered.index(h) for h in expected]
    assert indices == sorted(indices), "Headings out of order"


def test_operations_contains_markers():
    text = OPS.read_text(encoding="utf-8")
    assert "<!-- TLDR-START" in text and "<!-- TLDR-END" in text


def test_sources_yaml_exists():
    assert SRC.exists(), "runbook_sources.yml not found"
