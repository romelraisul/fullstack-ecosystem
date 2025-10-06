#!/usr/bin/env python3
"""
Type checking script using mypy with baseline support.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_python_command() -> str:
    """Get the current Python executable path."""
    # Use the virtual environment Python if available
    venv_python = Path("C:/Users/romel/.venv/Scripts/python.exe")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run_command(cmd: list[str], description: str, allow_failure: bool = False) -> bool:
    """Run a command and return its success status."""
    print(f"\n🔍 {description}...")
    try:
        # Set encoding for subprocess to handle unicode files
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace undecodable bytes
            env=env,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True
        else:
            if allow_failure:
                print(f"⚠️  {description} found issues")
            else:
                print(f"❌ {description} failed with return code {result.returncode}")
            return False

    except Exception as e:
        print(f"✗ Error running {description}: {e}")
        return False


def run_mypy_check(targets: list[str], baseline_mode: bool = False) -> bool:
    """Run mypy type checking on specified targets."""
    python_cmd = get_python_command()

    cmd = [python_cmd, "-m", "mypy"]

    if baseline_mode:
        # In baseline mode, we're more permissive and generate reports
        cmd.extend(["--ignore-missing-imports", "--show-error-codes", "--no-error-summary"])

    cmd.extend(targets)

    return run_command(cmd, "mypy type checking", allow_failure=True)


def generate_baseline(output_file: str = "mypy-baseline.txt") -> bool:
    """Generate a mypy baseline report."""
    python_cmd = get_python_command()

    print(f"\n📝 Generating mypy baseline report: {output_file}")

    # Run mypy on specific modules to avoid path issues
    modules = ["scripts/", "autogen/backend/", "src/", "tests/"]

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        all_output = []

        for module in modules:
            if Path(module).exists():
                print(f"  Checking {module}...")
                result = subprocess.run(
                    [
                        python_cmd,
                        "-m",
                        "mypy",
                        module,
                        "--ignore-missing-imports",
                        "--show-error-codes",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )

                all_output.append(f"\n=== {module} ===")
                if result.stdout:
                    all_output.append(result.stdout)
                if result.stderr:
                    all_output.append(f"STDERR: {result.stderr}")
                all_output.append(f"Return code: {result.returncode}")

        # Write baseline to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# mypy baseline - errors to be gradually fixed\n")
            f.write(f"# Generated with mypy {get_mypy_version()}\n")
            f.write("# Run 'python scripts/type_check.py --baseline' to regenerate\n")
            f.write("\n".join(all_output))

        print(f"✅ Baseline report generated: {output_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to generate baseline: {e}")
        return False


def get_mypy_version() -> str:
    """Get mypy version."""
    try:
        result = subprocess.run(
            [get_python_command(), "-m", "mypy", "--version"], capture_output=True, text=True
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def main() -> bool:
    """Main type checking function."""
    python_cmd = get_python_command()

    print("🔍 Running type checking with mypy...")
    print(f"Using Python: {python_cmd}")
    print(f"mypy version: {get_mypy_version()}")

    # Check command line arguments
    if len(sys.argv) > 1 and "--baseline" in sys.argv:
        return generate_baseline()

    # Get target files/directories from command line or use specific targets
    if len(sys.argv) > 1 and not any(arg.startswith("--") for arg in sys.argv[1:]):
        targets = sys.argv[1:]
    else:
        # Default to key directories that are more likely to be well-typed
        targets = [
            "scripts/quality.py",
            "scripts/format.py",
            "scripts/lint.py",
            "scripts/type_check.py",
        ]

    print(f"Type checking targets: {targets}")

    success = run_mypy_check(targets)

    if success:
        print("\n🎉 Type checking passed!")
        return True
    else:
        print("\n⚠️  Type checking found issues.")
        print("\n💡 Quick fix suggestions:")
        print("  1. Add type annotations to function signatures")
        print("  2. Use 'from typing import List, Dict, Optional' for type hints")
        print("  3. Run: python scripts/type_check.py --baseline  # Generate baseline")
        print("  4. Gradually fix type issues file by file")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
