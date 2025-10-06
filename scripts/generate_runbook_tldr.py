#!/usr/bin/env python3
"""Generate the TL;DR section in OPERATIONS.md between TLDR markers from canonical YAML.

Usage:
  python scripts/generate_runbook_tldr.py

Idempotent: re-writes only the block between <!-- TLDR-START --> and <!-- TLDR-END -->.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RE_START = re.compile(r"<!-- TLDR-START:.*?-->", re.IGNORECASE)
RE_END = re.compile(r"<!-- TLDR-END -->", re.IGNORECASE)

ROOT = Path(__file__).resolve().parents[1]
OPS_FILE = ROOT / "OPERATIONS.md"
SRC_FILE = ROOT / "docs" / "runbook_sources.yml"


def load_sources():
    with SRC_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_section(key: str, cfg: dict) -> str:
    heading = cfg.get("heading", key)
    ordered = cfg.get("ordered", False)
    items = cfg.get("items", [])
    lines = [f"### {heading}", ""]
    if isinstance(items, list):
        if ordered:
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item}")
        else:
            for item in items:
                if isinstance(item, dict):
                    # key: value style entries
                    for k, v in item.items():
                        lines.append(f"- {k}: `{v}`" if " " not in str(v) else f"- {k}: {v}")
                else:
                    lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def build_tldr(data: dict) -> str:
    sections_order = [
        "core_commands",
        "key_files",
        "add_agent",
        "dynamic_slo",
        "synthetic_traffic",
        "security_tracing",
        "troubleshoot",
        "escalation",
    ]
    parts = ["## Runbook TL;DR", ""]
    for sec in sections_order:
        if sec in data["sections"]:
            parts.append(format_section(sec, data["sections"][sec]))
    parts.append(
        "(Full details in subsequent sections. Regenerate with: `python scripts/generate_runbook_tldr.py`)"
    )
    parts.append("")
    return "\n".join(parts)


def replace_block(original: str, new_block: str) -> str:
    start_match = RE_START.search(original)
    end_match = RE_END.search(original)
    if not start_match or not end_match:
        raise SystemExit("TLDR markers not found in OPERATIONS.md")
    if end_match.start() < start_match.end():
        raise SystemExit("Malformed TLDR markers ordering")
    before = original[: start_match.end()] + "\n"
    after = original[end_match.start() :]
    # Preserve end marker; ensure we don't duplicate it
    # after already starts with <!-- TLDR-END -->
    return before + new_block + after


def main():
    data = load_sources()
    tldr = build_tldr(data)
    text = OPS_FILE.read_text(encoding="utf-8")
    new_text = replace_block(text, tldr + "\n")
    if new_text == text:
        print("TL;DR already up to date")
        return
    OPS_FILE.write_text(new_text, encoding="utf-8")
    print("Updated TL;DR section in OPERATIONS.md")


if __name__ == "__main__":
    main()
