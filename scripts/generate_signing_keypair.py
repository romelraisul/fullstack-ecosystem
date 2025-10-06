#!/usr/bin/env python3
"""Generate a new Ed25519 keypair for governance artifact signing.

Outputs (stdout):
  Seed (base64)  -> set as GOV_SIGNING_PRIVATE_KEY secret
  Public Key     -> distribute to verifiers / publish

Optional flags:
  --json  Emit machine readable JSON object with seed & public key

Security: Keep the seed secret. Rotate by generating a new keypair, updating
repository secret, and documenting rotation time. Retire old public key only
after previously signed artifacts exceed retention window.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys

try:
    from nacl import signing
except Exception:
    print("pynacl required: pip install pynacl", file=sys.stderr)
    raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sk = signing.SigningKey.generate()
    seed = sk._seed  # 32 bytes
    pk = sk.verify_key

    seed_b64 = base64.b64encode(seed).decode("ascii")
    pub_b64 = base64.b64encode(bytes(pk)).decode("ascii")

    if args.json:
        print(json.dumps({"seed_base64": seed_b64, "public_key_base64": pub_b64}, indent=2))
    else:
        print("Seed (base64) - store as GOV_SIGNING_PRIVATE_KEY:")
        print(seed_b64)
        print("\nPublic Key (base64) - share with verifiers:")
        print(pub_b64)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
