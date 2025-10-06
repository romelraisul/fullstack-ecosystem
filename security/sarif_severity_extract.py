#!/usr/bin/env python3
"""Extract precise severity counts from SARIF files produced by Trivy / Grype.

Logic:
- Prefer SARIF result.level mapping when available AND rule.defaultConfiguration.level gives a better normalized severity.
- Attempt to read result.properties.severity or result.properties.cvss.score / result.properties.cvss.severity.
- Map severities to standardized buckets: critical, high, medium, low, unknown.
- If CVSS score present (score >= 9.0 -> critical, >=7.0 -> high, >=4.0 -> medium, >=0.1 -> low).
- Provide counts per tool plus merged totals.
- Output JSON summary to stdout (or file if --output provided) with schema_version for future evolution.

Usage:
  python security/sarif_severity_extract.py --sarif trivy-image.sarif --sarif grype-image.sarif --output vuln-severity-summary.json

The script is resilient: it won't fail the pipeline on partial parsing; missing/invalid entries skipped.
"""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

SCHEMA_VERSION = "1.0"

BUCKETS = ["critical", "high", "medium", "low", "unknown"]


def score_to_bucket(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "unknown"


def normalize_sev(raw: str | None) -> str:
    if not raw:
        return "unknown"
    r = raw.lower()
    # common synonyms
    mapping = {
        "critical": "critical",
        "crit": "critical",
        "high": "high",
        "h": "high",
        "medium": "medium",
        "med": "medium",
        "moderate": "medium",
        "low": "low",
        "info": "low",
        "information": "low",
        "negligible": "low",
    }
    return mapping.get(r, "unknown")


def classify_result(result: Dict[str, Any], rules_index: Dict[str, Dict[str, Any]]) -> str:
    # 1) properties.severity
    props = result.get("properties") or {}
    if isinstance(props, dict):
        sev = props.get("severity")
        if sev:
            return normalize_sev(sev)
        # CVSS vector/score nested possibilities
        cvss = props.get("cvss")
        if isinstance(cvss, dict):
            sc = cvss.get("score")
            try:
                if sc is not None:
                    return score_to_bucket(float(sc))
            except (TypeError, ValueError):
                pass
    # 2) ruleId -> rule.defaultConfiguration.level
    rule_id = result.get("ruleId")
    if rule_id and rule_id in rules_index:
        rule = rules_index[rule_id]
        default_cfg = rule.get("defaultConfiguration") or {}
        level = default_cfg.get("level")
        if level:
            # Map SARIF level to severity bucket
            level_map = {"error": "high", "warning": "medium", "note": "low"}
            return level_map.get(level, "unknown")
    # 3) fallback to result.level
    level = result.get("level")
    if level:
        level_map = {"error": "high", "warning": "medium", "note": "low"}
        return level_map.get(level, "unknown")
    return "unknown"


def extract(file_path: Path) -> Dict[str, Any]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    counts = {b: 0 for b in BUCKETS}
    rules_index: Dict[str, Dict[str, Any]] = {}
    for run in data.get("runs", []):
        # index rules
        for rule in (run.get("tool", {}).get("driver", {}).get("rules") or []):
            rid = rule.get("id")
            if rid:
                rules_index[rid] = rule
        for res in run.get("results", []) as List[Dict[str, Any]]:
            bucket = classify_result(res, rules_index)
            counts[bucket] = counts.get(bucket, 0) + 1
    return {"file": str(file_path), "counts": counts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sarif", action="append", dest="sarif", help="SARIF file(s)", required=True)
    ap.add_argument("--output", help="Output JSON file (if omitted prints to stdout)")
    args = ap.parse_args()
    summaries = []
    aggregate = {b: 0 for b in BUCKETS}
    for f in args.sarif:
        path = Path(f)
        if not path.exists():
            continue
        try:
            summary = extract(path)
            summaries.append(summary)
            for b, c in summary["counts"].items():
                aggregate[b] = aggregate.get(b, 0) + c
        except Exception as e:  # noqa: BLE001
            summaries.append({"file": str(path), "error": str(e)})
    out = {
        "schema_version": SCHEMA_VERSION,
        "summaries": summaries,
        "aggregate": aggregate,
        "totals": {
            "critical": aggregate.get("critical", 0),
            "high": aggregate.get("high", 0),
            "critical_high_combined": aggregate.get("critical", 0) + aggregate.get("high", 0)
        }
    }
    content = json.dumps(out, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)

if __name__ == "__main__":
    main()
