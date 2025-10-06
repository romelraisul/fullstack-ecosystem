import base64
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

try:
    pass  # type: ignore
except Exception:  # pragma: no cover
    pytest.skip("pynacl not installed", allow_module_level=True)


def _write_checksums(tmpdir: pathlib.Path):
    data = {
        "generated_at": "2025-01-01T00:00:00Z",
        "artifacts": [
            {"path": "schemas/openapi-governance.json", "sha256": "a" * 64, "size": 1},
            {"path": "status/governance-summary.json", "sha256": "b" * 64, "size": 2},
        ],
        "aggregate_sha256": "c" * 64,
        "count": 2,
    }
    p = tmpdir / "checksums.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_sign_and_verify(tmp_path):
    from nacl import signing

    sk = signing.SigningKey.generate()
    seed = sk._seed  # 32 bytes
    env = os.environ.copy()
    env["GOV_SIGNING_PRIVATE_KEY"] = base64.b64encode(seed).decode("ascii")
    checksums = _write_checksums(tmp_path)
    sig_path = tmp_path / "checksums-signature.json"
    pub_out = tmp_path / "checksums-pubkey.txt"
    # Run sign script
    script = ROOT / "scripts" / "sign_checksums.py"
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "--checksums",
            str(checksums),
            "--out",
            str(sig_path),
            "--public-out",
            str(pub_out),
        ],
        env=env,
    )
    assert sig_path.exists()
    # Verify
    verify_script = ROOT / "scripts" / "verify_checksums_signature.py"
    subprocess.check_call(
        [
            sys.executable,
            str(verify_script),
            "--checksums",
            str(checksums),
            "--signature",
            str(sig_path),
        ]
    )
