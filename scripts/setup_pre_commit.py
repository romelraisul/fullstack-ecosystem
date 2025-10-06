#!/usr/bin/env python3
"""
Pre-commit setup script for fullstack-ecosystem project.
Installs and configures pre-commit hooks for code quality.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return its success status."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("OUTPUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error in {description}: {e}")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")

    required_packages = ["pre-commit", "pytest", "black", "ruff", "mypy", "flake8"]

    missing = []
    for package in required_packages:
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                check=True,
                capture_output=True,
            )
            print(f"✅ {package} is installed")
        except subprocess.CalledProcessError:
            missing.append(package)
            print(f"❌ {package} is missing")

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install them with: pip install " + " ".join(missing))
        return False

    print("✅ All required dependencies are installed")
    return True


def setup_pre_commit() -> bool:
    """Set up pre-commit hooks."""
    print("\n🎯 Setting up pre-commit hooks...")

    steps = [
        ([sys.executable, "-m", "pre_commit", "install"], "Installing pre-commit hooks"),
        (
            [sys.executable, "-m", "pre_commit", "install", "--hook-type", "pre-push"],
            "Installing pre-push hooks",
        ),
        ([sys.executable, "-m", "pre_commit", "autoupdate"], "Updating hook versions"),
    ]

    all_success = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_success = False

    return all_success


def test_pre_commit() -> bool:
    """Test pre-commit installation by running on a single file."""
    print("\n🧪 Testing pre-commit installation...")

    # Find a Python file to test with
    test_files = ["scripts/format.py", "scripts/lint.py", "scripts/type_check.py"]

    test_file = None
    for file in test_files:
        if Path(file).exists():
            test_file = file
            break

    if not test_file:
        print("⚠️  No test files found, skipping pre-commit test")
        return True

    # Run pre-commit on the test file
    cmd = [sys.executable, "-m", "pre_commit", "run", "--files", test_file]
    print(f"Testing with file: {test_file}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("Pre-commit test output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("✅ Pre-commit test completed (check output above for any issues)")
        return True
    except Exception as e:
        print(f"⚠️  Pre-commit test encountered an issue: {e}")
        return False


def main() -> bool:
    """Main setup function."""
    print("🚀 Setting up pre-commit hooks for fullstack-ecosystem")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path(".pre-commit-config.yaml").exists():
        print("❌ .pre-commit-config.yaml not found!")
        print("Please run this script from the project root directory.")
        return False

    # Check dependencies
    if not check_dependencies():
        return False

    # Setup pre-commit
    if not setup_pre_commit():
        print("\n❌ Pre-commit setup failed")
        return False

    # Test installation
    test_pre_commit()

    print("\n" + "=" * 60)
    print("🎉 Pre-commit setup completed!")
    print("\n📋 What's been configured:")
    print("  • Code formatting (black + ruff format)")
    print("  • Code linting (ruff + flake8)")
    print("  • Type checking (mypy)")
    print("  • Fast tests (pytest unit tests)")
    print("  • File validation (trailing whitespace, yaml, json, etc.)")
    print("  • Security scanning (bandit)")

    print("\n💡 Usage:")
    print("  • Hooks run automatically on git commit")
    print("  • Full quality check runs on git push")
    print("  • Manual run: pre-commit run --all-files")
    print("  • Skip hooks: git commit --no-verify")

    print("\n🔧 Management commands:")
    print("  • make pre-commit-install  # Reinstall hooks")
    print("  • make pre-commit-run      # Run on all files")
    print("  • make pre-commit-update   # Update hook versions")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
