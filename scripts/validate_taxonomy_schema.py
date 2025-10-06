#!/usr/bin/env python3
"""Validate alerts_taxonomy.json against alerts_taxonomy.schema.json.

Exit codes:
 0 = OK
 1 = Schema validation errors
 2 = File not found / other IO issue
"""

from __future__ import annotations

import json
import pathlib
import sys

from jsonschema import Draft7Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "alerts_taxonomy.schema.json"
TAX = ROOT / "alerts_taxonomy.json"


def main():
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        data = json.loads(TAX.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        print(f"Missing file: {e.filename}")
        sys.exit(2)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(2)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print("Schema validation failed:")
        for err in errors:
            loc = ".".join(str(p) for p in err.path)
            print(f" - {loc or '<root>'}: {err.message}")
        sys.exit(1)
    print("Schema validation OK")


if __name__ == "__main__":
    main()
