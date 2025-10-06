#!/usr/bin/env python3
"""
Pre-commit wrapper script to handle encoding and environment setup.
Ensures proper UTF-8 encoding and environment variables for quality scripts.
"""

import os
import subprocess
import sys


def setup_environment():
    """Set up environment for consistent execution."""
    # Force UTF-8 encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # Ensure scripts can find each other
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)


def run_script(script_name: str, args: list = None) -> int:
    """Run a script with proper environment setup."""
    setup_environment()

    if args is None:
        args = []

    # Build command
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    cmd = [sys.executable, script_path] + args

    # Run with proper encoding
    try:
        result = subprocess.run(
            cmd, env=os.environ.copy(), cwd=os.getcwd(), text=True, encoding="utf-8"
        )
        return result.returncode
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return 1


def main():
    """Main entry point for wrapper script."""
    if len(sys.argv) < 2:
        print("Usage: pre_commit_wrapper.py <script_name> [args...]")
        return 1

    script_name = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    return run_script(script_name, args)


if __name__ == "__main__":
    sys.exit(main())
