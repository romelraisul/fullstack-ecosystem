#!/usr/bin/env python
"""Exit non-zero if pip-audit JSON contains HIGH or CRITICAL vulns."""

from __future__ import annotations

import json
import pathlib
import sys

fail = False
for fn in ["pip-audit-platforms.json", "pip-audit-taxonomy.json"]:
    p = pathlib.Path(fn)
    if not p.exists():
        continue
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        print(f"Could not parse {fn}: {e}", file=sys.stderr)
        continue
    for dep in data.get("dependencies", []):
        name = dep.get("name")
        version = dep.get("version")
        for vul in dep.get("vulns", []):
            sev = (vul.get("severity") or "").lower()
            if sev in {"high", "critical"}:
                print(f"HIGH/CRITICAL: {name} {version} -> {vul.get('id')}")
                fail = True

if fail:
    sys.exit(1)
print("No high/critical vulnerabilities found.")
