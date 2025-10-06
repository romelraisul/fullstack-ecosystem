#!/usr/bin/env python3
"""
Code linting script using Ruff and Flake8.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_python_command():
    """Get the current Python executable path."""
    # Use the virtual environment Python if available
    venv_python = Path("C:/Users/romel/.venv/Scripts/python.exe")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run_command(cmd, description, allow_failure=False):
    """Run a command and return its success status."""
    print(f"\n🔍 {description}...")
    try:
        # Set encoding for subprocess to handle unicode files
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace undecodable bytes
            env=env,
        )
        print(f"✅ {description} passed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if allow_failure:
            print(f"⚠️  {description} found issues")
        else:
            print(f"❌ {description} failed")
        if e.stdout:
            print("OUTPUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Main linting function."""
    python_cmd = get_python_command()

    print("🔍 Running code linting...")
    print(f"Using Python: {python_cmd}")

    # Get target files/directories from command line or use current directory
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
        targets_str = " ".join(f'"{target}"' for target in targets)
    else:
        # Default to current directory
        targets_str = '"."'

    print(f"Linting targets: {targets_str}")

    results = []

    # Run ruff check (primary linter)
    ruff_success = run_command(
        f'"{python_cmd}" -m ruff check {targets_str}', "Ruff linting", allow_failure=True
    )
    results.append(("Ruff", ruff_success))

    # Run flake8 (secondary linter)
    flake8_success = run_command(
        f'"{python_cmd}" -m flake8 {targets_str}', "Flake8 linting", allow_failure=True
    )
    results.append(("Flake8", flake8_success))

    # Run mypy (type checking)
    mypy_success = run_command(
        f'"{python_cmd}" scripts/type_check.py {" ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""}',
        "mypy type checking",
        allow_failure=True,
    )
    results.append(("mypy", mypy_success))

    # Summary
    print("\n📊 Linting Summary:")
    all_passed = True
    for tool, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {tool}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        print("\n🎉 All linting checks passed!")
    else:
        print("\n⚠️  Some linting checks found issues. Please review and fix them.")
        print("\n💡 Quick fix suggestions:")
        print(f"  1. Run: {python_cmd} scripts/format.py  # Auto-fix formatting issues")
        print(f"  2. Run: {python_cmd} -m ruff check --fix .  # Auto-fix some ruff issues")
        print(f"  3. Run: {python_cmd} scripts/type_check.py --baseline  # Generate mypy baseline")
        print("  4. Add type annotations to fix mypy issues")
        print("  5. Manually review and fix remaining issues")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
