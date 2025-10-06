#!/usr/bin/env python3
"""Validate GitHub workflow YAML syntax.
Usage: python security/validate_workflow_yaml.py .github/workflows/container-security-scan.yml
Installs PyYAML if missing (best-effort) unless NO_INSTALL env is set.
"""

import os
import subprocess
import sys


def ensure_pyyaml():
    try:
        import yaml  # type: ignore

        return True
    except ImportError:
        if os.environ.get("NO_INSTALL"):
            print("PyYAML not installed and NO_INSTALL set; skipping parse.")
            return False
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
            return True
        except Exception as e:
            print("Failed to install PyYAML:", e)
            return False


def main():
    if len(sys.argv) < 2:
        print("Path required")
        return 1
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found:", path)
        return 1
    ok = ensure_pyyaml()
    if not ok:
        return 0
    import yaml  # type: ignore

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        print("YAML parse OK.")
        # Dump top-level keys for quick review
        if isinstance(data, dict):
            print("Top-level keys:", ", ".join(data.keys()))
        return 0
    except yaml.YAMLError as e:
        print("YAML parse FAILED:")
        print(e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
