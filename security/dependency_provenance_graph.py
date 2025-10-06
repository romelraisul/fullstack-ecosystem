#!/usr/bin/env python3
"""Emit a normalized dependency provenance graph from a requirements lock file.

Parses a pip-compile style requirements.txt with hashes and outputs JSON nodes:
  [{ name, version, line, hashes: [sha256:...] }]

Usage:
  python security/dependency_provenance_graph.py --lock requirements.txt --output dep-graph.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess

LINE_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([0-9][^\s;]+)")
HASH_RE = re.compile(r"--hash=sha256:([a-f0-9]{64})")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--lock", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()


def main():
    a = parse_args()
    nodes = []
    with open(a.lock, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.startswith(("#", "\n")):
                continue
            m = LINE_RE.search(line)
            if not m:
                continue
            name, version = m.group(1), m.group(2)
            hashes = HASH_RE.findall(line)
            nodes.append(
                {
                    "name": name.lower(),
                    "version": version,
                    "line": idx,
                    "hashes": [f"sha256:{h}" for h in hashes],
                }
            )
    # Attempt to collect edges via pipdeptree if installed in current env
    edges = []
    if shutil.which("pipdeptree"):
        try:
            result = subprocess.run(
                ["pipdeptree", "--json-tree"], capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)

            # data is a list of {package:{key:..}, dependencies:[...]}
            def walk(node):
                pkg = node.get("package", {})
                parent = pkg.get("key")
                for dep in node.get("dependencies", []):
                    child = dep.get("package", {}).get("key")
                    if parent and child:
                        edges.append({"from": parent, "to": child})
                    walk(dep)

            for entry in data:
                walk(entry)
        except Exception as e:
            print(f"[dep-graph] pipdeptree edge extraction failed: {e}")
    else:
        print("[dep-graph] pipdeptree not available; edges omitted")
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": "dep-graph-schema.v1",
                "nodes": nodes,
                "count": len(nodes),
                "edges": edges,
                "edge_count": len(edges),
            },
            f,
            indent=2,
        )
    print(f"[dep-graph] Wrote {len(nodes)} nodes, {len(edges)} edges -> {a.output}")


if __name__ == "__main__":
    main()
