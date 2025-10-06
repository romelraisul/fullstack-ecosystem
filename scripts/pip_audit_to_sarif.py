#!/usr/bin/env python
"""Convert pip-audit JSON output(s) to SARIF for code scanning upload."""

from __future__ import annotations

import json
import pathlib


def convert(in_file: str, sarif_file: str) -> None:
    p = pathlib.Path(in_file)
    if not p.exists():
        return
    data = json.loads(p.read_text())
    rules = {}
    results = []
    for dep in data.get("dependencies", []):
        name = dep.get("name")
        version = dep.get("version")
        for vul in dep.get("vulns", []):
            rule_id = vul.get("id") or f"UNKNOWN-{name}"
            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "name": rule_id,
                    "shortDescription": {"text": (vul.get("description") or "")[:120]},
                    "fullDescription": {"text": vul.get("description") or ""},
                    "help": {
                        "text": vul.get("fix_version") or "",
                        "markdown": vul.get("description") or "",
                    },
                }
            severity = (vul.get("severity") or "").lower()
            level = "error" if severity in {"critical", "high"} else "warning"
            results.append(
                {
                    "ruleId": rule_id,
                    "level": level,
                    "message": {"text": f"{name} {version} vulnerable: {rule_id}"},
                    "locations": [],
                }
            )
    sarif = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "pip-audit", "rules": list(rules.values())}},
                "results": results,
            }
        ],
    }
    pathlib.Path(sarif_file).write_text(json.dumps(sarif, indent=2))


if __name__ == "__main__":
    convert("pip-audit-platforms.json", "pip-audit-platforms.sarif")
    convert("pip-audit-taxonomy.json", "pip-audit-taxonomy.sarif")
