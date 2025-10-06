"""Compare current Trivy SARIF results against stored baseline and emit drift report.

Usage:
  python security/compare_vuln_baseline.py \
    --sarif trivy-image.sarif \
    --baseline security/vuln_baseline.json \
    --update-baseline false

Exit Codes:
  0 - No new CRITICAL vulnerabilities detected (or baseline updated successfully)
  2 - New CRITICAL vulnerabilities detected (drift)
  3 - SARIF parsing error / invalid input

If --update-baseline true is passed (typically on a trusted main branch after human review),
the baseline file is rewritten with the current set of critical vulnerabilities.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_sarif_critical_vulns(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover - fatal
        print(f"ERROR: Failed to parse SARIF: {e}", file=sys.stderr)
        sys.exit(3)

    critical_ids: set[str] = set()
    runs = data.get("runs", [])
    for run in runs:
        tool = run.get("tool", {})
        driver = tool.get("driver", {})
        rules = {r.get("id"): r for r in driver.get("rules", []) if isinstance(r, dict)}
        results = run.get("results", [])
        for res in results:
            rule_id = res.get("ruleId") or res.get("rule", {}).get("id")
            if not rule_id:
                continue
            # Some SARIF producers add severity in properties or level
            properties = res.get("properties", {})
            severity = properties.get("security-severity") or properties.get("severity")
            # Fallback: check rule metadata
            if not severity and rule_id in rules:
                severity = rules[rule_id].get("properties", {}).get("problem.severity")
            if severity and str(severity).upper() == "CRITICAL":
                location_key = _result_location_signature(res)
                critical_ids.add(f"{rule_id}:{location_key}")
    return critical_ids


def _result_location_signature(result: dict[str, Any]) -> str:
    locs = result.get("locations", [])
    if not locs:
        return "(no-location)"
    loc = locs[0]
    phys = loc.get("physicalLocation", {})
    artifact = phys.get("artifactLocation", {}).get("uri", "unknown")
    region = phys.get("region", {})
    start_line = region.get("startLine", 0)
    return f"{artifact}:{start_line}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sarif", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--update-baseline", dest="update_baseline", action="store_true")
    args = parser.parse_args()

    sarif_path = Path(args.sarif)
    base_path = Path(args.baseline)

    if not sarif_path.exists():
        print(f"ERROR: SARIF file not found: {sarif_path}", file=sys.stderr)
        return 3

    current = load_sarif_critical_vulns(sarif_path)

    if base_path.exists():
        try:
            baseline_data = json.loads(base_path.read_text(encoding="utf-8"))
            baseline_set = set(baseline_data.get("critical_vulnerabilities", []))
        except Exception as e:
            print(f"WARN: Failed to parse baseline ({e}); treating as empty.")
            baseline_set = set()
    else:
        baseline_set = set()

    new_criticals = sorted(current - baseline_set)

    if new_criticals and not args.update_baseline:
        print("NEW CRITICAL VULNERABILITIES DETECTED (Drift):")
        for cid in new_criticals:
            print(f"  - {cid}")
        print("Failing build to enforce baseline drift policy.")
        return 2

    if args.update_baseline:
        updated = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "critical_vulnerabilities": sorted(current),
        }
        base_path.parent.mkdir(parents=True, exist_ok=True)
        base_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
        print(f"Baseline updated: {base_path} ({len(current)} critical entries)")
        return 0

    print("No new CRITICAL vulnerabilities relative to baseline.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
