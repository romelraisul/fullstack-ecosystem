#!/usr/bin/env python3
"""Verify a checksums signature produced by sign_checksums.py.

Usage:
  python scripts/verify_checksums_signature.py --checksums status/checksums.json \
      --signature status/checksums-signature.json [--public-key base64_pubkey]

If --public-key not supplied it will be read from signature JSON.

Exit codes:
 0 success
 1 failure (verification mismatch)
 2 usage / file errors
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys

try:
    from nacl import signing
except Exception:  # pragma: no cover
    print("pynacl required (pip install pynacl)", file=sys.stderr)
    raise


def load_json(path: str):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"Missing file: {path}", file=sys.stderr)
        raise SystemExit(2)
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checksums", required=True)
    ap.add_argument("--signature", required=True)
    ap.add_argument("--public-key", help="Override public key (base64)")
    args = ap.parse_args()

    checksums = load_json(args.checksums)
    sigdoc = load_json(args.signature)

    agg = checksums.get("aggregate_sha256")
    count = checksums.get("count")
    if agg is None or count is None:
        print("checksums.json missing aggregate_sha256 or count", file=sys.stderr)
        return 2

    fmt_version = sigdoc.get("signature_format_version", 1)
    if fmt_version == 1:
        payload_obj = {"aggregate_sha256": agg, "count": count}
    else:
        # v2 expects artifact list to be present in checksums (artifacts array with path & sha256)
        artifacts = checksums.get("artifacts") or []
        canon = []
        for a in artifacts:
            p = a.get("path")
            h = a.get("sha256")
            if p and h:
                canon.append({"path": p, "sha256": h})
        canon.sort(key=lambda x: x["path"])
        payload_obj = {"aggregate_sha256": agg, "count": count, "artifacts": canon}

    canonical = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

    pub_b64 = args.public_key or sigdoc.get("public_key_base64")
    if not pub_b64:
        print("Public key not provided and absent in signature", file=sys.stderr)
        return 2
    sig_b64 = sigdoc.get("signature_base64")
    if not sig_b64:
        print("Signature missing in signature JSON", file=sys.stderr)
        return 2

    try:
        pub_bytes = base64.b64decode(pub_b64)
        sig_bytes = base64.b64decode(sig_b64)
    except Exception as e:  # pragma: no cover
        print(f"Base64 decode error: {e}", file=sys.stderr)
        return 2

    try:
        vk = signing.VerifyKey(pub_bytes)
        vk.verify(canonical, sig_bytes)
    except Exception as e:
        print(f"VERIFY_FAIL: {e}", file=sys.stderr)
        return 1

    print("VERIFY_OK")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
