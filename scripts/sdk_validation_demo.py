#!/usr/bin/env python3
"""
SDK Validation Integration Demo

This script demonstrates the complete SDK validation workflow,
including package creation, validation, and reporting.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from create_simple_demo import create_simple_demo_package
from validate_sdk_publishing import SDKValidationReport, SDKValidator


def run_comprehensive_validation_demo() -> dict[str, Any]:
    """
    Run a comprehensive demonstration of the SDK validation system.

    Returns:
        Dictionary containing demo results and metrics.
    """
    print("🚀 Starting SDK Validation System Demo")
    print("=" * 50)

    demo_results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "demo_version": "1.0.0",
        "packages_tested": [],
        "validation_reports": [],
        "summary": {},
    }

    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix="sdk_validation_demo_")
    print(f"📁 Demo directory: {temp_dir}")

    try:
        # Test 1: Create and validate a well-structured package
        print("\n🧪 Test 1: Well-structured package validation")
        good_package_path = create_simple_demo_package(temp_dir)
        good_report = validate_package(good_package_path, "Good Package")

        demo_results["packages_tested"].append(
            {
                "name": "Well-structured Package",
                "path": good_package_path,
                "expected_status": "pass",
            }
        )
        demo_results["validation_reports"].append(good_report.to_dict())

        # Test 2: Create and validate a minimal package (should have warnings)
        print("\n🧪 Test 2: Minimal package validation")
        minimal_package_path = create_minimal_package(temp_dir)
        minimal_report = validate_package(minimal_package_path, "Minimal Package")

        demo_results["packages_tested"].append(
            {"name": "Minimal Package", "path": minimal_package_path, "expected_status": "warning"}
        )
        demo_results["validation_reports"].append(minimal_report.to_dict())

        # Test 3: Create and validate a problematic package (should fail)
        print("\n🧪 Test 3: Problematic package validation")
        problematic_package_path = create_problematic_package(temp_dir)
        problematic_report = validate_package(problematic_package_path, "Problematic Package")

        demo_results["packages_tested"].append(
            {
                "name": "Problematic Package",
                "path": problematic_package_path,
                "expected_status": "fail",
            }
        )
        demo_results["validation_reports"].append(problematic_report.to_dict())

        # Generate summary
        demo_results["summary"] = generate_demo_summary(demo_results["validation_reports"])

        # Test 4: Demonstrate CLI functionality
        print("\n🧪 Test 4: CLI validation demo")
        demonstrate_cli_validation(good_package_path)

        print("\n📊 Demo Summary")
        print_demo_summary(demo_results)

        return demo_results

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        demo_results["error"] = str(e)
        return demo_results

    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up demo directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️  Could not clean up demo directory: {e}")


def validate_package(package_path: str, package_name: str) -> SDKValidationReport:
    """Validate a package and display results."""
    print(f"   📦 Validating: {package_name}")
    print(f"   📍 Path: {package_path}")

    validator = SDKValidator()
    report = validator.validate_all(package_path)

    summary = report.get_summary()
    print(
        f"   📊 Results: {report.overall_status.upper()} "
        f"(✅{summary['pass']} ⚠️{summary['warning']} ❌{summary['fail']})"
    )

    # Show key issues
    critical_issues = [
        r for r in report.results if r.severity in ["critical", "high"] and r.status == "fail"
    ]
    if critical_issues:
        print("   🚨 Critical Issues:")
        for issue in critical_issues[:3]:  # Show top 3
            print(f"      • {issue.name}: {issue.message}")

    return report


def create_minimal_package(base_dir: str) -> str:
    """Create a minimal package with basic files only."""
    package_dir = Path(base_dir) / "minimal-package"
    package_dir.mkdir(exist_ok=True)

    # Only create minimal files
    with open(package_dir / "README.md", "w", encoding="utf-8") as f:
        f.write("# Minimal Package\n\nA minimal package for testing.")

    # Create minimal Python file
    (package_dir / "main.py").write_text(
        'def hello():\n    return "Hello, World!"\n', encoding="utf-8"
    )

    print(f"   📦 Created minimal package at: {package_dir}")
    return str(package_dir)


def create_problematic_package(base_dir: str) -> str:
    """Create a package with various issues for testing validation failures."""
    package_dir = Path(base_dir) / "problematic-package"
    package_dir.mkdir(exist_ok=True)

    # Create minimal README
    with open(package_dir / "README.md", "w", encoding="utf-8") as f:
        f.write("# Problematic Package\n\nThis package has issues.")

    # Create Python file with hardcoded secrets
    problematic_code = """
# This file contains security issues for testing
API_KEY = "sk-1234567890abcdef"  # Hardcoded secret
password = "my-secret-password"  # Another secret

def get_data():
    return {"api_key": API_KEY}
"""

    with open(package_dir / "problematic.py", "w", encoding="utf-8") as f:
        f.write(problematic_code)

    # Create sensitive files
    with open(package_dir / "private.key", "w", encoding="utf-8") as f:
        f.write("-----BEGIN PRIVATE KEY-----\nPrivate key content\n-----END PRIVATE KEY-----")

    with open(package_dir / ".env", "w", encoding="utf-8") as f:
        f.write("SECRET_KEY=super-secret-value\nDATABASE_PASSWORD=admin123")

    # Create setup.py with syntax error
    broken_setup = """
from setuptools import setup

setup(
    name="problematic-package"
    version="1.0.0"  # Missing comma - syntax error
    description="A package with issues"
)
"""

    with open(package_dir / "setup.py", "w", encoding="utf-8") as f:
        f.write(broken_setup)

    print(f"   📦 Created problematic package at: {package_dir}")
    return str(package_dir)


def demonstrate_cli_validation(package_path: str):
    """Demonstrate CLI validation functionality."""
    print(f"   🖥️  Running CLI validation on: {Path(package_path).name}")

    try:
        # Run validation via CLI
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_sdk_publishing.py",
                package_path,
                "--output",
                "cli-validation-report.json",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )

        if result.returncode == 0:
            print("   ✅ CLI validation successful")
            if os.path.exists("cli-validation-report.json"):
                with open("cli-validation-report.json") as f:
                    cli_report = json.load(f)
                print(
                    f"   📄 Report generated: {cli_report['package_name']} v{cli_report['version']}"
                )
                os.remove("cli-validation-report.json")  # Clean up
        else:
            print(f"   ❌ CLI validation failed: {result.stderr}")

    except Exception as e:
        print(f"   ⚠️  CLI demonstration skipped: {e}")


def generate_demo_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate summary statistics from validation reports."""
    summary = {
        "total_packages": len(reports),
        "status_distribution": {"pass": 0, "warning": 0, "fail": 0, "critical": 0},
        "total_checks": 0,
        "total_passes": 0,
        "total_warnings": 0,
        "total_failures": 0,
        "common_issues": [],
    }

    all_failures = []

    for report in reports:
        # Count status distribution
        status = report["overall_status"]
        summary["status_distribution"][status] = summary["status_distribution"].get(status, 0) + 1

        # Aggregate check counts
        report_summary = report["summary"]
        summary["total_checks"] += sum(report_summary.values())
        summary["total_passes"] += report_summary.get("pass", 0)
        summary["total_warnings"] += report_summary.get("warning", 0)
        summary["total_failures"] += report_summary.get("fail", 0)

        # Collect failures for common issue analysis
        for result in report["results"]:
            if result["status"] == "fail":
                all_failures.append(result["name"])

    # Find common issues
    failure_counts = {}
    for failure in all_failures:
        failure_counts[failure] = failure_counts.get(failure, 0) + 1

    # Get most common issues
    common_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
    summary["common_issues"] = [
        {"issue": issue, "count": count} for issue, count in common_failures[:5]  # Top 5
    ]

    return summary


def print_demo_summary(demo_results: dict[str, Any]):
    """Print a formatted demo summary."""
    summary = demo_results["summary"]

    print("=" * 50)
    print(f"📋 Packages Tested: {summary['total_packages']}")
    print(f"🔍 Total Validation Checks: {summary['total_checks']}")
    print(f"✅ Total Passes: {summary['total_passes']}")
    print(f"⚠️  Total Warnings: {summary['total_warnings']}")
    print(f"❌ Total Failures: {summary['total_failures']}")

    print("\n📊 Package Status Distribution:")
    for status, count in summary["status_distribution"].items():
        if count > 0:
            emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌", "critical": "🚨"}
            print(f"   {emoji.get(status, '❓')} {status.title()}: {count}")

    if summary["common_issues"]:
        print("\n🔍 Most Common Issues:")
        for issue_data in summary["common_issues"]:
            issue, count = issue_data["issue"], issue_data["count"]
            print(f"   • {issue} ({count} packages)")

    print("\n💡 Recommendations:")
    print("   • Ensure all packages have README, LICENSE, and setup files")
    print("   • Implement comprehensive test coverage")
    print("   • Use security scanning tools to detect sensitive data")
    print("   • Follow semantic versioning guidelines")
    print("   • Include proper CI/CD configuration")

    print("=" * 50)


def save_demo_results(demo_results: dict[str, Any], output_file: str = None):
    """Save demo results to JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sdk_validation_demo_results_{timestamp}.json"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(demo_results, f, indent=2)

        print(f"💾 Demo results saved to: {output_file}")
        return output_file

    except Exception as e:
        print(f"⚠️  Could not save demo results: {e}")
        return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SDK Validation System Integration Demo")
    parser.add_argument(
        "--save-results", action="store_true", help="Save demo results to JSON file"
    )
    parser.add_argument("--output-file", help="Output file for demo results (if saving)")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    if args.quiet:
        # Redirect stdout to reduce output
        import contextlib
        import io

        stdout_backup = sys.stdout
        with contextlib.redirect_stdout(io.StringIO()):
            demo_results = run_comprehensive_validation_demo()
        sys.stdout = stdout_backup

        # Print only summary
        print_demo_summary(demo_results)
    else:
        demo_results = run_comprehensive_validation_demo()

    if args.save_results:
        save_demo_results(demo_results, args.output_file)

    print("\n🎉 SDK Validation Demo Complete!")

    # Return appropriate exit code based on demo success
    if "error" in demo_results:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
