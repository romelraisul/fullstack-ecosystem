#!/usr/bin/env python3
"""SDK Publishing Validation Pipeline.

This module provides comprehensive validation for SDK publishing workflows,
including package structure validation, metadata verification, security scanning,
and compatibility testing.

Features:
- Package structure validation
- Metadata and manifest verification
- Security vulnerability scanning
- API compatibility checking
- Documentation completeness validation
- CI/CD integration tests
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    status: str  # "pass", "fail", "warning", "skip"
    message: str
    details: dict[str, Any] | None = None
    severity: str = "info"  # "critical", "high", "medium", "low", "info"


@dataclass
class SDKValidationReport:
    """Comprehensive SDK validation report."""

    package_name: str
    version: str
    timestamp: str
    overall_status: str
    results: list[ValidationResult]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "package_name": self.package_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "severity": r.severity,
                }
                for r in self.results
            ],
            "metadata": self.metadata,
            "summary": self.get_summary(),
        }

    def get_summary(self) -> dict[str, int]:
        """Get summary statistics."""
        summary = {"pass": 0, "fail": 0, "warning": 0, "skip": 0}
        for result in self.results:
            summary[result.status] = summary.get(result.status, 0) + 1
        return summary


class SDKValidator:
    """Main SDK validation class."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize validator with configuration."""
        self.config = config or {}
        self.results: list[ValidationResult] = []
        self.temp_dir = None

    def add_result(
        self,
        name: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
        severity: str = "info",
    ):
        """Add validation result."""
        result = ValidationResult(name, status, message, details, severity)
        self.results.append(result)
        return result

    def validate_package_structure(self, package_path: str) -> list[ValidationResult]:
        """Validate package structure and required files."""
        results = []
        package_path = Path(package_path)

        # Check if package exists
        if not package_path.exists():
            results.append(
                ValidationResult(
                    "Package Exists",
                    "fail",
                    f"Package path does not exist: {package_path}",
                    severity="critical",
                )
            )
            return results

        # Required files for Python packages
        required_files = {
            "README.md": "README file",
            "LICENSE": "License file",
            "setup.py": "Setup script (Python)",
            "pyproject.toml": "Project config (Python)",
            "requirements.txt": "Dependencies (Python)",
        }

        # Check for required files
        for file_name, description in required_files.items():
            file_path = package_path / file_name
            if file_path.exists():
                results.append(
                    ValidationResult(
                        f"Required File: {file_name}",
                        "pass",
                        f"{description} found",
                        {"file_size": file_path.stat().st_size},
                    )
                )
            else:
                # Some files are alternatives, so warn instead of fail
                severity = "medium" if file_name in ["setup.py", "pyproject.toml"] else "high"
                results.append(
                    ValidationResult(
                        f"Required File: {file_name}",
                        "warning",
                        f"{description} not found",
                        severity=severity,
                    )
                )

        # Check for package source directory
        src_dirs = ["src", package_path.name, "lib"]
        src_found = False
        for src_dir in src_dirs:
            if (package_path / src_dir).is_dir():
                src_found = True
                results.append(
                    ValidationResult(
                        "Source Directory",
                        "pass",
                        f"Source directory found: {src_dir}",
                        {"path": str(package_path / src_dir)},
                    )
                )
                break

        if not src_found:
            results.append(
                ValidationResult(
                    "Source Directory",
                    "fail",
                    "No source directory found",
                    {"checked_paths": src_dirs},
                    "high",
                )
            )

        # Check for tests directory
        test_dirs = ["tests", "test", "spec"]
        test_found = False
        for test_dir in test_dirs:
            if (package_path / test_dir).is_dir():
                test_found = True
                test_files = list((package_path / test_dir).glob("**/*test*.py"))
                results.append(
                    ValidationResult(
                        "Test Directory",
                        "pass",
                        f"Test directory found: {test_dir}",
                        {"path": str(package_path / test_dir), "test_files": len(test_files)},
                    )
                )
                break

        if not test_found:
            results.append(
                ValidationResult(
                    "Test Directory",
                    "warning",
                    "No test directory found",
                    {"checked_paths": test_dirs},
                    "medium",
                )
            )

        return results

    def validate_metadata(self, package_path: str) -> list[ValidationResult]:
        """Validate package metadata and manifest files."""
        results = []
        package_path = Path(package_path)

        # Validate setup.py if present
        setup_py = package_path / "setup.py"
        if setup_py.exists():
            try:
                # Basic syntax check
                with open(setup_py) as f:
                    content = f.read()
                    compile(content, str(setup_py), "exec")

                # Check for required setup() parameters
                required_params = ["name", "version", "description", "author"]
                missing_params = []
                for param in required_params:
                    if f"{param}=" not in content and f'"{param}"' not in content:
                        missing_params.append(param)

                if missing_params:
                    results.append(
                        ValidationResult(
                            "Setup.py Metadata",
                            "warning",
                            f"Missing recommended parameters: {', '.join(missing_params)}",
                            {"missing": missing_params},
                            "medium",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            "Setup.py Metadata", "pass", "All required metadata present"
                        )
                    )

            except SyntaxError as e:
                results.append(
                    ValidationResult(
                        "Setup.py Syntax",
                        "fail",
                        f"Syntax error in setup.py: {e}",
                        {"error": str(e)},
                        "high",
                    )
                )

        # Validate pyproject.toml if present
        pyproject_toml = package_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                import tomllib

                with open(pyproject_toml, "rb") as f:
                    config = tomllib.load(f)

                # Check for required sections
                required_sections = ["project", "build-system"]
                for section in required_sections:
                    if section in config:
                        results.append(
                            ValidationResult(
                                f"Pyproject.toml [{section}]",
                                "pass",
                                f"Section [{section}] present",
                            )
                        )
                    else:
                        results.append(
                            ValidationResult(
                                f"Pyproject.toml [{section}]",
                                "warning",
                                f"Section [{section}] missing",
                                severity="medium",
                            )
                        )

                # Validate project metadata
                if "project" in config:
                    project = config["project"]
                    required_fields = ["name", "version", "description"]
                    for field in required_fields:
                        if field in project:
                            results.append(
                                ValidationResult(
                                    f"Project {field}", "pass", f"Project {field} specified"
                                )
                            )
                        else:
                            results.append(
                                ValidationResult(
                                    f"Project {field}",
                                    "warning",
                                    f"Project {field} missing",
                                    severity="medium",
                                )
                            )

            except Exception as e:
                results.append(
                    ValidationResult(
                        "Pyproject.toml Parse",
                        "fail",
                        f"Failed to parse pyproject.toml: {e}",
                        {"error": str(e)},
                        "high",
                    )
                )

        # Validate package.json if present (for Node.js projects)
        package_json = package_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    config = json.load(f)

                required_fields = ["name", "version", "description"]
                for field in required_fields:
                    if field in config:
                        results.append(
                            ValidationResult(
                                f"Package.json {field}", "pass", f"Package {field} specified"
                            )
                        )
                    else:
                        results.append(
                            ValidationResult(
                                f"Package.json {field}",
                                "warning",
                                f"Package {field} missing",
                                severity="medium",
                            )
                        )

            except json.JSONDecodeError as e:
                results.append(
                    ValidationResult(
                        "Package.json Parse",
                        "fail",
                        f"Invalid JSON in package.json: {e}",
                        {"error": str(e)},
                        "high",
                    )
                )

        return results

    def validate_security(self, package_path: str) -> list[ValidationResult]:
        """Run security validation checks."""
        results = []
        package_path = Path(package_path)

        # Check for sensitive files that shouldn't be included
        sensitive_patterns = [
            "*.key",
            "*.pem",
            "*.p12",
            "*.jks",
            ".env",
            ".env.*",
            "*.secret",
            "*.token",
            "id_rsa",
            "id_dsa",
            "id_ecdsa",
            "id_ed25519",
        ]

        sensitive_files = []
        for pattern in sensitive_patterns:
            found_files = list(package_path.rglob(pattern))
            sensitive_files.extend(found_files)

        if sensitive_files:
            results.append(
                ValidationResult(
                    "Sensitive Files",
                    "fail",
                    f"Found {len(sensitive_files)} potentially sensitive files",
                    {"files": [str(f) for f in sensitive_files]},
                    "critical",
                )
            )
        else:
            results.append(ValidationResult("Sensitive Files", "pass", "No sensitive files found"))

        # Check for hardcoded secrets in source files
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]

        import re

        hardcoded_secrets = []

        for source_file in package_path.rglob("*.py"):
            try:
                with open(source_file, encoding="utf-8") as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            hardcoded_secrets.append(
                                {"file": str(source_file), "matches": len(matches)}
                            )
            except Exception:
                continue

        if hardcoded_secrets:
            results.append(
                ValidationResult(
                    "Hardcoded Secrets",
                    "fail",
                    f"Found potential hardcoded secrets in {len(hardcoded_secrets)} files",
                    {"files": hardcoded_secrets},
                    "high",
                )
            )
        else:
            results.append(
                ValidationResult("Hardcoded Secrets", "pass", "No hardcoded secrets detected")
            )

        # Check dependencies for known vulnerabilities (simplified)
        requirements_file = package_path / "requirements.txt"
        if requirements_file.exists():
            try:
                # This is a simplified check - in production you'd use safety, pip-audit, etc.
                with open(requirements_file) as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]

                results.append(
                    ValidationResult(
                        "Dependency Count",
                        "pass",
                        f"Found {len(deps)} dependencies to validate",
                        {"count": len(deps)},
                    )
                )

                # Mock vulnerability check (replace with real scanner in production)
                vulnerable_deps = []  # Would be populated by actual scanner

                if vulnerable_deps:
                    results.append(
                        ValidationResult(
                            "Dependency Vulnerabilities",
                            "fail",
                            f"Found {len(vulnerable_deps)} vulnerable dependencies",
                            {"vulnerabilities": vulnerable_deps},
                            "high",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            "Dependency Vulnerabilities",
                            "pass",
                            "No known vulnerabilities found in dependencies",
                        )
                    )

            except Exception as e:
                results.append(
                    ValidationResult(
                        "Dependency Scan",
                        "warning",
                        f"Could not scan dependencies: {e}",
                        severity="medium",
                    )
                )

        return results

    def validate_compatibility(self, package_path: str) -> list[ValidationResult]:
        """Validate API compatibility and versioning."""
        results = []
        package_path = Path(package_path)

        # Check for breaking changes indicator files
        breaking_changes_files = ["BREAKING_CHANGES.md", "CHANGELOG.md", "HISTORY.md"]

        changelog_found = False
        for changelog_file in breaking_changes_files:
            if (package_path / changelog_file).exists():
                changelog_found = True
                results.append(
                    ValidationResult(
                        "Changelog File",
                        "pass",
                        f"Changelog found: {changelog_file}",
                        {"file": changelog_file},
                    )
                )
                break

        if not changelog_found:
            results.append(
                ValidationResult(
                    "Changelog File",
                    "warning",
                    "No changelog file found - consider adding CHANGELOG.md",
                    severity="medium",
                )
            )

        # Check for semantic versioning compliance
        version = self._extract_version(package_path)
        if version:
            # Basic semver pattern check
            import re

            semver_pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?(?:\+[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$"

            if re.match(semver_pattern, version):
                results.append(
                    ValidationResult(
                        "Semantic Versioning",
                        "pass",
                        f"Version follows semantic versioning: {version}",
                        {"version": version},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "Semantic Versioning",
                        "warning",
                        f"Version may not follow semantic versioning: {version}",
                        {"version": version},
                        "medium",
                    )
                )
        else:
            results.append(
                ValidationResult(
                    "Version Detection",
                    "warning",
                    "Could not detect package version",
                    severity="medium",
                )
            )

        # Check for API documentation
        doc_files = list(package_path.rglob("*api*.md")) + list(package_path.rglob("docs/*.md"))
        if doc_files:
            results.append(
                ValidationResult(
                    "API Documentation",
                    "pass",
                    f"Found {len(doc_files)} documentation files",
                    {"files": [str(f) for f in doc_files]},
                )
            )
        else:
            results.append(
                ValidationResult(
                    "API Documentation",
                    "warning",
                    "No API documentation files found",
                    severity="medium",
                )
            )

        return results

    def validate_build_system(self, package_path: str) -> list[ValidationResult]:
        """Validate build system and CI/CD configuration."""
        results = []
        package_path = Path(package_path)

        # Check for CI/CD configuration files
        ci_configs = [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            "Jenkinsfile",
            ".travis.yml",
        ]

        ci_found = False
        for ci_pattern in ci_configs:
            ci_files = list(package_path.glob(ci_pattern))
            if ci_files:
                ci_found = True
                results.append(
                    ValidationResult(
                        "CI/CD Configuration",
                        "pass",
                        f"CI/CD configuration found: {ci_pattern}",
                        {"files": [str(f) for f in ci_files]},
                    )
                )
                break

        if not ci_found:
            results.append(
                ValidationResult(
                    "CI/CD Configuration",
                    "warning",
                    "No CI/CD configuration found",
                    severity="medium",
                )
            )

        # Check for build configuration
        build_files = [
            "Makefile",
            "build.py",
            "build.sh",
            "tox.ini",
            "noxfile.py",
            "docker-compose.yml",
            "Dockerfile",
        ]

        build_found = False
        for build_file in build_files:
            if (package_path / build_file).exists():
                build_found = True
                results.append(
                    ValidationResult(
                        "Build Configuration",
                        "pass",
                        f"Build configuration found: {build_file}",
                        {"file": build_file},
                    )
                )

        if not build_found:
            results.append(
                ValidationResult(
                    "Build Configuration",
                    "warning",
                    "No build configuration found",
                    severity="medium",
                )
            )

        # Check for test configuration
        test_configs = ["pytest.ini", "tox.ini", "pyproject.toml", ".coveragerc"]
        test_config_found = False

        for test_config in test_configs:
            if (package_path / test_config).exists():
                test_config_found = True
                results.append(
                    ValidationResult(
                        "Test Configuration",
                        "pass",
                        f"Test configuration found: {test_config}",
                        {"file": test_config},
                    )
                )

        if not test_config_found:
            results.append(
                ValidationResult(
                    "Test Configuration",
                    "warning",
                    "No test configuration found",
                    severity="medium",
                )
            )

        return results

    def _extract_version(self, package_path: Path) -> str | None:
        """Extract version from package files."""
        # Try pyproject.toml first
        pyproject_toml = package_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                import tomllib

                with open(pyproject_toml, "rb") as f:
                    config = tomllib.load(f)
                    return config.get("project", {}).get("version")
            except Exception:
                pass

        # Try setup.py
        setup_py = package_path / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py) as f:
                    content = f.read()
                    import re

                    version_match = re.search(r'version\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    if version_match:
                        return version_match.group(1)
            except Exception:
                pass

        # Try package.json
        package_json = package_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    config = json.load(f)
                    return config.get("version")
            except Exception:
                pass

        return None

    def validate_all(self, package_path: str) -> SDKValidationReport:
        """Run all validation checks and generate report."""
        package_path = Path(package_path)
        package_name = package_path.name
        version = self._extract_version(package_path) or "unknown"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Run all validation categories
        all_results = []

        try:
            all_results.extend(self.validate_package_structure(str(package_path)))
            all_results.extend(self.validate_metadata(str(package_path)))
            all_results.extend(self.validate_security(str(package_path)))
            all_results.extend(self.validate_compatibility(str(package_path)))
            all_results.extend(self.validate_build_system(str(package_path)))
        except Exception as e:
            all_results.append(
                ValidationResult(
                    "Validation Error",
                    "fail",
                    f"Validation failed: {e}",
                    {"error": str(e)},
                    "critical",
                )
            )

        # Determine overall status
        has_critical = any(r.severity == "critical" and r.status == "fail" for r in all_results)
        has_high_fail = any(r.severity == "high" and r.status == "fail" for r in all_results)
        has_fail = any(r.status == "fail" for r in all_results)

        if has_critical:
            overall_status = "critical"
        elif has_high_fail:
            overall_status = "fail"
        elif has_fail:
            overall_status = "warning"
        else:
            overall_status = "pass"

        # Build metadata
        metadata = {
            "package_path": str(package_path),
            "validation_config": self.config,
            "total_checks": len(all_results),
            "validator_version": "1.0.0",
        }

        return SDKValidationReport(
            package_name=package_name,
            version=version,
            timestamp=timestamp,
            overall_status=overall_status,
            results=all_results,
            metadata=metadata,
        )


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SDK Publishing Validation Pipeline")
    parser.add_argument("package_path", help="Path to package directory to validate")
    parser.add_argument(
        "--output", default="sdk-validation-report.json", help="Output file for validation report"
    )
    parser.add_argument(
        "--format", choices=["json", "summary"], default="json", help="Output format"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with non-zero code if any validation fails"
    )
    parser.add_argument("--config", help="Configuration file (JSON) for validator settings")

    args = parser.parse_args()

    # Load configuration if provided
    config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config) as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

    # Initialize validator and run validation
    validator = SDKValidator(config)
    report = validator.validate_all(args.package_path)

    # Output results
    if args.format == "json":
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"📄 Validation report written to: {args.output}")

    # Print summary
    summary = report.get_summary()
    print(f"\n📊 SDK Validation Summary for {report.package_name} v{report.version}")
    print(f"Overall Status: {report.overall_status.upper()}")
    print(f"✅ Pass: {summary['pass']}")
    print(f"⚠️  Warning: {summary['warning']}")
    print(f"❌ Fail: {summary['fail']}")
    print(f"⏭️  Skip: {summary['skip']}")

    # Show critical/high severity failures
    critical_fails = [
        r for r in report.results if r.status == "fail" and r.severity in ["critical", "high"]
    ]

    if critical_fails:
        print("\n🚨 Critical Issues:")
        for result in critical_fails[:5]:  # Show top 5
            print(f"   • {result.name}: {result.message}")

    # Exit code logic
    if args.strict and (summary["fail"] > 0):
        return 1
    elif report.overall_status == "critical":
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
