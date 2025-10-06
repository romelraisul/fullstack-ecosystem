#!/usr/bin/env python3
"""
Code formatting script using Black and Ruff.
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


def run_command(cmd, description):
    """Run a command and return its success status."""
    print(f"\n🔧 {description}...")
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
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Main formatting function."""
    python_cmd = get_python_command()

    print("🎨 Running code formatting...")
    print(f"Using Python: {python_cmd}")

    # Get target files/directories from command line or use current directory
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
        targets_str = " ".join(f'"{target}"' for target in targets)
    else:
        # Default to current directory
        targets_str = '"."'

    print(f"Formatting targets: {targets_str}")

    success = True

    # Run ruff format (replaces need for black in most cases)
    if not run_command(f'"{python_cmd}" -m ruff format {targets_str}', "Ruff formatting"):
        success = False

    # Run ruff --fix for auto-fixable issues
    if not run_command(f'"{python_cmd}" -m ruff check --fix {targets_str}', "Ruff auto-fixes"):
        success = False

    # Run black as backup/alternative
    if not run_command(f'"{python_cmd}" -m black {targets_str}', "Black formatting"):
        success = False

    if success:
        print("\n🎉 All formatting completed successfully!")
    else:
        print("\n⚠️  Some formatting steps failed. Please check the output above.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
