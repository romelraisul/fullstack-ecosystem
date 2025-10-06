#!/usr/bin/env python3
"""Sign checksums.json with an Ed25519 key.

Inputs:
  --checksums  Path to checksums.json (default: status/checksums.json)
  --out        Output signature JSON file (default: status/checksums-signature.json)
  --public-out Optional path to write derived public key (if not already managed) (default: status/checksums-pubkey.txt)

Environment:
  GOV_SIGNING_PRIVATE_KEY  Base64 encoded 32-byte Ed25519 private key seed.

Output signature JSON shape (v2):
{
    "algorithm": "Ed25519",
    "signature_format_version": 2,
    "signed_at": ISO8601 UTC,
    "artifact": "checksums.json",
    "aggregate_sha256": <repeat from checksums.json>,
    "count": <count>,
    "artifacts": [ {"path": ..., "sha256": ...}, ... ],
    "signature_base64": <raw signature over canonical payload>,
    "public_key_base64": <public key>,
    "canonical_payload": { ... },
    "payload_encoding": "json+sorted+compact"
}

Canonical payload to sign (UTF-8 bytes, v2):
    JSON serialization (sorted keys, compact separators) of:
        {
            "aggregate_sha256": <value>,
            "count": <count>,
            "artifacts": [ {"path": p, "sha256": h}, ... sorted by path ]
        }

Backward compatibility: if future tooling needs to verify legacy v1 signatures they only cover
{"aggregate_sha256": <value>, "count": <count>} with no artifacts list.

Requires: pynacl
"""

from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import pathlib
import sys

try:
    from nacl import signing
except Exception:  # pragma: no cover - import guard
    print("ERROR: pynacl is required for signing (pip install pynacl)", file=sys.stderr)
    raise


def load_private_key_from_env(var: str = "GOV_SIGNING_PRIVATE_KEY") -> signing.SigningKey:
    b64 = os.getenv(var)
    if not b64:
        raise SystemExit(f"Environment variable {var} is not set")
    try:
        seed = base64.b64decode(b64.strip())
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"Failed to base64 decode {var}: {e}")
    if len(seed) != 32:
        raise SystemExit(f"Decoded {var} length {len(seed)} != 32 (expected Ed25519 seed)")
    return signing.SigningKey(seed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checksums", default="status/checksums.json")
    ap.add_argument("--out", default="status/checksums-signature.json")
    ap.add_argument("--public-out", default="status/checksums-pubkey.txt")
    args = ap.parse_args()

    cpath = pathlib.Path(args.checksums)
    if not cpath.exists():
        print(f"Checksums file {cpath} missing; nothing to sign", file=sys.stderr)
        return 0

    data = json.loads(cpath.read_text(encoding="utf-8"))
    agg = data.get("aggregate_sha256")
    count = data.get("count")
    artifacts = data.get("artifacts") or []
    if not agg:
        raise SystemExit("checksums.json missing aggregate_sha256")
    if count is None:
        raise SystemExit("checksums.json missing count")

    # Canonical payload v2 includes artifact path/hash list (path + sha256 only) sorted by path
    canon_artifacts = []
    for a in artifacts:
        p = a.get("path")
        h = a.get("sha256")
        if p and h:
            canon_artifacts.append({"path": p, "sha256": h})
    canon_artifacts.sort(key=lambda x: x["path"])
    payload_obj = {"aggregate_sha256": agg, "count": count, "artifacts": canon_artifacts}
    canonical = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

    sk = load_private_key_from_env()
    pk = sk.verify_key
    sig = sk.sign(canonical).signature

    signature_b64 = base64.b64encode(sig).decode("ascii")
    pub_b64 = base64.b64encode(bytes(pk)).decode("ascii")

    out_payload = {
        "algorithm": "Ed25519",
        "signature_format_version": 2,
        "signed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "artifact": cpath.name,
        "aggregate_sha256": agg,
        "count": count,
        "artifacts": canon_artifacts,
        "signature_base64": signature_b64,
        "public_key_base64": pub_b64,
        "canonical_payload": payload_obj,
        "payload_encoding": "json+sorted+compact",
    }

    opath = pathlib.Path(args.out)
    opath.write_text(json.dumps(out_payload, indent=2), encoding="utf-8")

    # Write separate public key file for convenience if requested
    if args.public_out:
        pathlib.Path(args.public_out).write_text(pub_b64 + "\n", encoding="utf-8")

    print(f"Signed {cpath} -> {opath}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
