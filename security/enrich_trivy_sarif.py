#!/usr/bin/env python3
"""Lightweight SARIF enrichment: add synthetic layer property to results if absent.

Usage: enrich_trivy_sarif.py --sarif trivy-image.sarif --image <image_ref>

The layer value is a stable sha256: prefix + first 12 hex chars of sha1(ruleId+image).
Safe to run multiple times (idempotent; will not overwrite existing layer property).
"""

import argparse
import hashlib
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--sarif", required=True)
parser.add_argument("--image", required=True)
args = parser.parse_args()

path = args.sarif
image = args.image
try:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"[enrich] unable to read SARIF: {e}", file=sys.stderr)
    sys.exit(0)

added = 0
for run in data.get("runs", []):
    for res in run.get("results", []) or []:
        props = res.setdefault("properties", {})
        if "layer" in props:
            continue
        rid = res.get("ruleId", "UNKNOWN")
        h = hashlib.sha1(f"{rid}{image}".encode()).hexdigest()[:12]
        props["layer"] = "sha256:" + h
        added += 1

try:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"[enrich] added layer property to {added} results")
except Exception as e:
    print(f"[enrich] failed to write SARIF: {e}", file=sys.stderr)
    sys.exit(1)
