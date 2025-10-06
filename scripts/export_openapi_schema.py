"""Export the FastAPI OpenAPI schema to a versioned JSON file.

Usage:
  python scripts/export_openapi_schema.py [--out openapi-governance.json]

The script imports the FastAPI app from governance_app.app, generates the schema
via app.openapi(), injects a generated timestamp, and writes it to the target file.

Intended to be run in CI so the resulting artifact can be published (e.g. uploaded
as a workflow artifact or committed back to the repo if desired).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export governance OpenAPI schema")
    parser.add_argument(
        "--out", default="openapi-governance.json", help="Output path for schema JSON"
    )
    args = parser.parse_args()

    try:
        from governance_app.app import app  # type: ignore
    except Exception as e:  # pragma: no cover - import failure clarity
        print(f"Failed to import FastAPI app: {e}", file=sys.stderr)
        return 1

    schema = app.openapi()
    # Override version if env var present
    version_env = os.getenv("GOVERNANCE_VERSION")
    if version_env:
        schema.setdefault("info", {})["version"] = version_env
    # Inject metadata helpful for consumers
    schema["x-generated-at"] = datetime.now(timezone.utc).isoformat()
    schema["x-governance-version"] = schema.get("info", {}).get("version", "0.0.0")

    out_path = Path(args.out)
    out_path.write_text(json.dumps(schema, indent=2, sort_keys=True))
    print(f"Wrote OpenAPI schema to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
