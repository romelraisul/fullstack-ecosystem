"""Vulnerability severity gating for pip-audit output.

Reads pip_audit_report.json (pip-audit --format json) and enforces a
severity threshold unless ALLOW_VULNERABILITIES=true.

Environment Variables:
  VULN_SEVERITY_THRESHOLD: LOW|MEDIUM|HIGH|CRITICAL (default HIGH)
  ALLOW_VULNERABILITIES: true/false to override failing build

Exit Codes:
  0 - Pass (no vulns >= threshold OR override active)
  1 - Fail (vulns >= threshold and no override)
"""

from __future__ import annotations

import json
import os
from typing import Any


def load_report(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("No pip_audit_report.json generated; exiting (treat as pass)")
        return []


def normalize_severities(vuln: dict[str, Any]) -> list[str]:
    sev = vuln.get("severity")
    if isinstance(sev, str):
        return [sev.upper()]
    if isinstance(sev, list):
        return [str(s).upper() for s in sev]
    return []


def main() -> int:
    allow = os.getenv("ALLOW_VULNERABILITIES", "").lower() == "true"
    threshold = os.getenv("VULN_SEVERITY_THRESHOLD", "HIGH").upper()
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if threshold not in order:
        print(f"Unknown threshold '{threshold}', defaulting to HIGH")
        threshold = "HIGH"
    threshold_idx = order.index(threshold)

    data = load_report("pip_audit_report.json")
    failing: list[dict[str, Any]] = []
    for dep in data:
        vulns = dep.get("vulns") or []
        for v in vulns:
            svs = normalize_severities(v)
            if any(order.index(s) >= threshold_idx for s in svs if s in order):
                failing.append(
                    {
                        "name": dep.get("name"),
                        "version": dep.get("version"),
                        "id": v.get("id"),
                        "severity": svs,
                        "fix_versions": v.get("fix_versions"),
                    }
                )

    report = {
        "threshold": threshold,
        "failing_count": len(failing),
        "failing": failing,
    }
    print(json.dumps(report, indent=2))

    if failing and not allow:
        print(f"::error::{len(failing)} vulnerabilities >= {threshold} detected")
        return 1
    if failing and allow:
        print(
            f"::warning::{len(failing)} vulnerabilities >= {threshold} allowed by override (ALLOW_VULNERABILITIES=true)"
        )
    else:
        print("No vulnerabilities meeting or exceeding threshold")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
