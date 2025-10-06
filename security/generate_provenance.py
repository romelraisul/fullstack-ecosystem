#!/usr/bin/env python3
"""Generate a lightweight provenance JSON for an image build.

Now extended (v0.3) to include:
    - git commit
    - build timestamp UTC
    - image slug
    - build command (string) if supplied
    - scanner versions (Trivy / Grype) if supplied
    - sbom diff counts (if present)
    - sha256 digest of CycloneDX + SPDX SBOMs
    - environment (python)

Usage:
    python security/generate_provenance.py --image-slug SLUG --commit SHA \
            --cyclonedx sbom-SLUG.cdx.json --spdx sbom-SLUG.spdx.json \
            --diff sbom-diff-SLUG.json --output provenance-SLUG.json \
            [--build-command "docker build ..."] [--trivy-version V] [--grype-version V]

Exit codes: 0 success, 1 failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = "provenance-schema.v1"


def sha256(path: str) -> str | None:
    if not path or not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--image-slug", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--cyclonedx", required=False)
    p.add_argument("--spdx", required=False)
    p.add_argument("--diff", required=False)
    p.add_argument("--output", required=True)
    p.add_argument("--build-command", required=False)
    p.add_argument("--trivy-version", required=False)
    p.add_argument("--grype-version", required=False)
    p.add_argument(
        "--write-signature",
        action="store_true",
        help="If set, write provenance JSON sha256 digest to <output>.sha256 and embed under materials.signature",
    )
    p.add_argument(
        "--build-args-file",
        required=False,
        help="Path to file listing build args key=value used during docker build",
    )
    p.add_argument(
        "--reproducible-digest",
        required=False,
        help="Digest from a reproducibility re-build comparison step (if matched)",
    )
    return p.parse_args()


def main():
    a = parse_args()
    diff_counts = {}
    if a.diff and os.path.isfile(a.diff):
        try:
            with open(a.diff, encoding="utf-8") as f:
                diff = json.load(f)
            diff_counts = diff.get("meta", {}).get("counts", {})
        except Exception as e:  # pragma: no cover
            print(f"[prov] Failed to read diff: {e}", file=sys.stderr)

    build_args_list = []
    if a.build_args_file and os.path.isfile(a.build_args_file):
        try:
            with open(a.build_args_file, encoding="utf-8") as bf:
                for line in bf:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    build_args_list.append(line)
        except Exception as e:  # pragma: no cover
            print(f"[prov] Failed reading build args file: {e}", file=sys.stderr)

    prov = {
        "schema_version": SCHEMA_VERSION,
        "type": "provenance.v0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "image_slug": a.image_slug,
        "git_commit": a.commit,
        "build": {
            "command": a.build_command,
            "args": build_args_list or None,
        },
        "materials": {
            "cyclonedx": {
                "path": a.cyclonedx,
                "sha256": sha256(a.cyclonedx) if a.cyclonedx else None,
            },
            "spdx": {
                "path": a.spdx,
                "sha256": sha256(a.spdx) if a.spdx else None,
            },
            "signature": None,  # populated if --write-signature
        },
        "scanners": {
            "trivy": a.trivy_version,
            "grype": a.grype_version,
        },
        "sbom_diff": diff_counts,
        "build_env": {
            "python_version": sys.version.split()[0],
        },
        "future": {
            "slsa": "upgrade-planned",
            "reproducibility": {
                "rebuilt_digest": a.reproducible_digest,
                "status": "unknown" if not a.reproducible_digest else "matched",
            },
        },
    }

    os.makedirs(os.path.dirname(a.output) or ".", exist_ok=True)
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(prov, f, indent=2)
    print(f"[prov] Wrote provenance {a.output}")

    # Optionally write detached digest signature (simple sha256) and embed reference
    if a.write_signature:
        try:
            digest = sha256(a.output)
            sig_path = a.output + ".sha256"
            with open(sig_path, "w", encoding="utf-8") as sf:
                sf.write(digest + "\n")
            # embed after writing
            prov["materials"]["signature"] = {
                "path": os.path.basename(sig_path),
                "sha256": digest,
                "algorithm": "sha256",
            }
            # rewrite provenance including signature embedding
            with open(a.output, "w", encoding="utf-8") as f:
                json.dump(prov, f, indent=2)
            print(f"[prov] Wrote signature {sig_path}")
        except Exception as e:  # pragma: no cover
            print(f"[prov] Failed to write signature: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
