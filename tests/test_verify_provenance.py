import hashlib
import json
import os
import tempfile

from security.verify_provenance import verify_provenance


def write(path, data: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    return h.hexdigest()


def base_prov(tmp, with_sig=True):
    cdx = os.path.join(tmp, "sbom.cdx.json")
    write(cdx, "{}")
    spdx = os.path.join(tmp, "sbom.spdx.json")
    write(spdx, "{}")
    prov_path = os.path.join(tmp, "prov.json")
    prov = {
        "schema_version": "provenance-schema.v1",
        "type": "provenance.v0",
        "generated": "2025-01-01T00:00:00Z",
        "image_slug": "img",
        "git_commit": "deadbeef",
        "build": {"command": "docker build ."},
        "materials": {
            "cyclonedx": {"path": "sbom.cdx.json", "sha256": sha256(cdx)},
            "spdx": {"path": "sbom.spdx.json", "sha256": sha256(spdx)},
        },
        "scanners": {"trivy": "v0", "grype": "v0"},
        "sbom_diff": {"added": [], "removed": [], "version_changed": [], "hash_changed": []},
        "build_env": {"python_version": "3.x"},
        "future": {"slsa": "upgrade-planned"},
    }
    write(prov_path, json.dumps(prov, indent=2))
    if with_sig:
        digest = sha256(prov_path)
        sig_path = prov_path + ".sha256"
        write(sig_path, digest + "\n")
        prov["materials"]["signature"] = {
            "path": os.path.basename(sig_path),
            "sha256": digest,
            "algorithm": "sha256",
        }
        write(prov_path, json.dumps(prov, indent=2))
    return prov_path


def test_verify_success():
    with tempfile.TemporaryDirectory() as tmp:
        prov_path = base_prov(tmp, with_sig=True)
        code, errors = verify_provenance(prov_path)
        assert code == 0, errors
        assert not errors


def test_hash_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        prov_path = base_prov(tmp, with_sig=True)
        # Corrupt one SBOM file
        with open(os.path.join(tmp, "sbom.cdx.json"), "w") as f:
            f.write('{"changed":true}')
        code, errors = verify_provenance(prov_path)
        assert code == 1
        assert any("hash mismatch cyclonedx" in e for e in errors)


def test_signature_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        prov_path = base_prov(tmp, with_sig=True)
        # Modify provenance after signature
        with open(prov_path, "a") as f:
            f.write("\n")
        code, errors = verify_provenance(prov_path)
        assert code == 1
        assert any("embedded signature mismatch" in e for e in errors)


def test_missing_schema_version():
    with tempfile.TemporaryDirectory() as tmp:
        prov_path = base_prov(tmp, with_sig=True)
        # Remove schema_version
        with open(prov_path, encoding="utf-8") as f:
            data = json.load(f)
        data.pop("schema_version", None)
        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        code, errors = verify_provenance(prov_path)
        assert code == 1
        assert any("missing schema_version" in e for e in errors)
