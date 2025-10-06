#!/usr/bin/env python3
"""
Combined code quality script that runs both formatting and linting.
"""

import subprocess
import sys
from pathlib import Path


def run_script(script_name, description):
    """Run a Python script and return its success status."""
    print(f"\n{'=' * 60}")
    print(f"🚀 {description}")
    print("=" * 60)

    script_path = Path(__file__).parent / script_name
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main function to run code quality checks."""
    print("🎯 Running comprehensive code quality checks...")

    # Run formatting first
    format_success = run_script("format.py", "Code Formatting")

    # Run linting after formatting
    lint_success = run_script("lint.py", "Code Linting")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 FINAL SUMMARY")
    print("=" * 60)

    print(f"🎨 Formatting: {'✅ PASSED' if format_success else '❌ FAILED'}")
    print(f"🔍 Linting:    {'✅ PASSED' if lint_success else '❌ FAILED'}")

    if format_success and lint_success:
        print("\n🎉 All code quality checks passed! Your code is ready to go! 🚀")
        return True
    else:
        print("\n⚠️  Some code quality checks failed. Please review the output above.")
        print("\n💡 Next steps:")
        if not format_success:
            print("  1. Review formatting errors and fix manually if needed")
        if not lint_success:
            print("  2. Review linting errors and fix the issues")
        print("  3. Re-run this script to verify fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
