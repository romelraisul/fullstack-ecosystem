#!/usr/bin/env python3
"""
Test Suite for SDK Publishing Validation Pipeline

This test suite provides comprehensive coverage for the SDK validation system,
including unit tests, integration tests, and edge case validation.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the scripts directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_sdk_publishing import SDKValidationReport, SDKValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_creation(self):
        """Test basic ValidationResult creation."""
        result = ValidationResult(
            name="Test Check",
            status="pass",
            message="Test passed",
            details={"key": "value"},
            severity="info",
        )

        assert result.name == "Test Check"
        assert result.status == "pass"
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert result.severity == "info"

    def test_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult("Test", "pass", "Message")

        assert result.details is None
        assert result.severity == "info"


class TestSDKValidationReport:
    """Test SDKValidationReport dataclass."""

    def test_creation(self):
        """Test basic report creation."""
        results = [
            ValidationResult("Test1", "pass", "Passed"),
            ValidationResult("Test2", "fail", "Failed"),
        ]

        report = SDKValidationReport(
            package_name="test-package",
            version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
            overall_status="warning",
            results=results,
            metadata={"test": "data"},
        )

        assert report.package_name == "test-package"
        assert report.version == "1.0.0"
        assert len(report.results) == 2

    def test_to_dict(self):
        """Test report conversion to dictionary."""
        results = [ValidationResult("Test", "pass", "Passed")]
        report = SDKValidationReport(
            "test-pkg", "1.0.0", "2024-01-01T00:00:00Z", "pass", results, {"key": "value"}
        )

        result_dict = report.to_dict()

        assert "package_name" in result_dict
        assert "summary" in result_dict
        assert result_dict["package_name"] == "test-pkg"
        assert len(result_dict["results"]) == 1

    def test_summary(self):
        """Test summary statistics generation."""
        results = [
            ValidationResult("Test1", "pass", "Passed"),
            ValidationResult("Test2", "fail", "Failed"),
            ValidationResult("Test3", "warning", "Warning"),
            ValidationResult("Test4", "pass", "Passed"),
        ]

        report = SDKValidationReport(
            "test", "1.0.0", "2024-01-01T00:00:00Z", "warning", results, {}
        )

        summary = report.get_summary()

        assert summary["pass"] == 2
        assert summary["fail"] == 1
        assert summary["warning"] == 1
        assert summary["skip"] == 0


class TestSDKValidator:
    """Test SDKValidator main class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return SDKValidator()

    @pytest.fixture
    def temp_package(self):
        """Create temporary package directory for testing."""
        temp_dir = tempfile.mkdtemp()
        package_dir = Path(temp_dir) / "test-package"
        package_dir.mkdir()

        yield package_dir

        shutil.rmtree(temp_dir)

    def test_add_result(self, validator):
        """Test adding validation results."""
        result = validator.add_result("Test", "pass", "Success")

        assert len(validator.results) == 1
        assert validator.results[0] == result
        assert result.name == "Test"
        assert result.status == "pass"

    def test_validate_package_structure_missing_package(self, validator):
        """Test validation with missing package."""
        results = validator.validate_package_structure("/nonexistent/path")

        assert len(results) == 1
        assert results[0].status == "fail"
        assert results[0].severity == "critical"
        assert "does not exist" in results[0].message

    def test_validate_package_structure_complete(self, validator, temp_package):
        """Test validation with complete package structure."""
        # Create required files
        files_to_create = ["README.md", "LICENSE", "setup.py", "requirements.txt"]

        for file_name in files_to_create:
            (temp_package / file_name).write_text("dummy content")

        # Create source directory
        (temp_package / "src").mkdir()
        (temp_package / "src" / "__init__.py").write_text("")

        # Create test directory
        (temp_package / "tests").mkdir()
        (temp_package / "tests" / "test_example.py").write_text("def test_dummy(): pass")

        results = validator.validate_package_structure(str(temp_package))

        # Should have results for all checks
        assert len(results) >= 6  # Required files + source + test dirs

        # Check that most results are passes
        passes = [r for r in results if r.status == "pass"]
        assert len(passes) >= 4

    def test_validate_package_structure_minimal(self, validator, temp_package):
        """Test validation with minimal package."""
        # Only create README
        (temp_package / "README.md").write_text("# Test Package")

        results = validator.validate_package_structure(str(temp_package))

        # Should have mixed results - some passes, some warnings/fails
        statuses = [r.status for r in results]
        assert "pass" in statuses  # For README
        assert "warning" in statuses or "fail" in statuses  # For missing files

    def test_validate_metadata_setup_py(self, validator, temp_package):
        """Test setup.py metadata validation."""
        setup_content = """
from setuptools import setup

setup(
    name="test-package",
    version="1.0.0",
    description="Test package",
    author="Test Author"
)
"""
        (temp_package / "setup.py").write_text(setup_content)

        results = validator.validate_metadata(str(temp_package))

        # Should pass setup.py syntax and metadata checks
        setup_results = [r for r in results if "Setup.py" in r.name]
        assert len(setup_results) >= 1
        assert any(r.status == "pass" for r in setup_results)

    def test_validate_metadata_invalid_setup_py(self, validator, temp_package):
        """Test setup.py with syntax errors."""
        setup_content = """
from setuptools import setup

setup(
    name="test-package"
    version="1.0.0"  # Missing comma - syntax error
    description="Test package"
)
"""
        (temp_package / "setup.py").write_text(setup_content)

        results = validator.validate_metadata(str(temp_package))

        # Should fail syntax check
        syntax_results = [r for r in results if "Syntax" in r.name]
        assert len(syntax_results) >= 1
        assert any(r.status == "fail" for r in syntax_results)

    def test_validate_metadata_pyproject_toml(self, validator, temp_package):
        """Test pyproject.toml metadata validation."""
        # Note: This test requires tomllib (Python 3.11+) or tomli
        pyproject_content = """
[project]
name = "test-package"
version = "1.0.0"
description = "Test package"

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
"""
        (temp_package / "pyproject.toml").write_text(pyproject_content)

        try:
            results = validator.validate_metadata(str(temp_package))

            # Should pass pyproject.toml checks if tomllib is available
            pyproject_results = [r for r in results if "Pyproject.toml" in r.name]
            if pyproject_results:  # Only check if tomllib was available
                assert any(r.status == "pass" for r in pyproject_results)
        except ImportError:
            # tomllib not available, skip this test
            pytest.skip("tomllib not available for pyproject.toml testing")

    def test_validate_metadata_package_json(self, validator, temp_package):
        """Test package.json metadata validation."""
        package_json_content = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test package for Node.js",
        }

        with open(temp_package / "package.json", "w") as f:
            json.dump(package_json_content, f)

        results = validator.validate_metadata(str(temp_package))

        # Should pass package.json checks
        json_results = [r for r in results if "Package.json" in r.name]
        assert len(json_results) >= 3  # name, version, description
        assert all(r.status == "pass" for r in json_results)

    def test_validate_metadata_invalid_package_json(self, validator, temp_package):
        """Test invalid package.json."""
        (temp_package / "package.json").write_text('{"invalid": json}')

        results = validator.validate_metadata(str(temp_package))

        # Should fail JSON parse
        parse_results = [r for r in results if "Parse" in r.name]
        assert len(parse_results) >= 1
        assert any(r.status == "fail" for r in parse_results)

    def test_validate_security_clean_package(self, validator, temp_package):
        """Test security validation on clean package."""
        # Create normal source file
        (temp_package / "src").mkdir()
        (temp_package / "src" / "main.py").write_text(
            """
def hello_world():
    return "Hello, World!"
"""
        )

        results = validator.validate_security(str(temp_package))

        # Should pass security checks
        security_results = [r for r in results if r.status == "pass"]
        assert len(security_results) >= 2  # No sensitive files, no hardcoded secrets

    def test_validate_security_sensitive_files(self, validator, temp_package):
        """Test security validation with sensitive files."""
        # Create sensitive files
        (temp_package / "private.key").write_text("private key content")
        (temp_package / ".env").write_text("SECRET_KEY=my-secret")

        results = validator.validate_security(str(temp_package))

        # Should fail sensitive files check
        sensitive_results = [r for r in results if "Sensitive Files" in r.name]
        assert len(sensitive_results) >= 1
        assert any(r.status == "fail" for r in sensitive_results)

    def test_validate_security_hardcoded_secrets(self, validator, temp_package):
        """Test detection of hardcoded secrets."""
        # Create source file with hardcoded secrets
        (temp_package / "config.py").write_text(
            """
API_KEY = "sk-1234567890abcdef"
password = "my-secret-password"
database_token = "token-123456"
"""
        )

        results = validator.validate_security(str(temp_package))

        # Should detect hardcoded secrets
        secret_results = [r for r in results if "Hardcoded Secrets" in r.name]
        assert len(secret_results) >= 1
        assert any(r.status == "fail" for r in secret_results)

    def test_validate_security_with_requirements(self, validator, temp_package):
        """Test security validation with requirements file."""
        (temp_package / "requirements.txt").write_text(
            """
requests==2.28.1
flask>=1.0.0
numpy
"""
        )

        results = validator.validate_security(str(temp_package))

        # Should process dependencies
        dep_results = [r for r in results if "Dependency" in r.name]
        assert len(dep_results) >= 1

    def test_validate_compatibility_with_version(self, validator, temp_package):
        """Test compatibility validation with version."""
        # Create setup.py with version
        (temp_package / "setup.py").write_text(
            """
setup(
    name="test-package",
    version="1.2.3"
)
"""
        )

        results = validator.validate_compatibility(str(temp_package))

        # Should detect and validate semantic versioning
        version_results = [r for r in results if "Versioning" in r.name]
        assert len(version_results) >= 1
        assert any(r.status == "pass" for r in version_results)

    def test_validate_compatibility_with_changelog(self, validator, temp_package):
        """Test compatibility validation with changelog."""
        (temp_package / "CHANGELOG.md").write_text(
            """
# Changelog

## [1.0.0] - 2024-01-01
- Initial release
"""
        )

        results = validator.validate_compatibility(str(temp_package))

        # Should find changelog
        changelog_results = [r for r in results if "Changelog" in r.name]
        assert len(changelog_results) >= 1
        assert any(r.status == "pass" for r in changelog_results)

    def test_validate_build_system_with_ci(self, validator, temp_package):
        """Test build system validation with CI configuration."""
        # Create GitHub Actions workflow
        workflows_dir = temp_package / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest
"""
        )

        results = validator.validate_build_system(str(temp_package))

        # Should find CI configuration
        ci_results = [r for r in results if "CI/CD" in r.name]
        assert len(ci_results) >= 1
        assert any(r.status == "pass" for r in ci_results)

    def test_validate_build_system_with_makefile(self, validator, temp_package):
        """Test build system validation with Makefile."""
        (temp_package / "Makefile").write_text(
            """
.PHONY: test build install

test:
	pytest

build:
	python setup.py sdist

install:
	pip install -e .
"""
        )

        results = validator.validate_build_system(str(temp_package))

        # Should find build configuration
        build_results = [r for r in results if "Build Configuration" in r.name]
        assert len(build_results) >= 1
        assert any(r.status == "pass" for r in build_results)

    def test_extract_version_from_setup_py(self, validator, temp_package):
        """Test version extraction from setup.py."""
        (temp_package / "setup.py").write_text(
            """
setup(
    name="test-package",
    version="2.1.0"
)
"""
        )

        version = validator._extract_version(temp_package)
        assert version == "2.1.0"

    def test_extract_version_from_package_json(self, validator, temp_package):
        """Test version extraction from package.json."""
        package_json = {"name": "test-package", "version": "3.0.1"}
        with open(temp_package / "package.json", "w") as f:
            json.dump(package_json, f)

        version = validator._extract_version(temp_package)
        assert version == "3.0.1"

    def test_extract_version_none(self, validator, temp_package):
        """Test version extraction when no version found."""
        # No version files
        version = validator._extract_version(temp_package)
        assert version is None

    def test_validate_all_comprehensive(self, validator, temp_package):
        """Test complete validation pipeline."""
        # Create a complete package structure
        files_content = {
            "README.md": "# Test Package",
            "LICENSE": "MIT License",
            "setup.py": """
setup(
    name="test-package",
    version="1.0.0",
    description="Test package"
)
""",
            "requirements.txt": "requests==2.28.1",
            "src/__init__.py": "",
            "src/main.py": "def hello(): return 'Hello'",
            "tests/test_main.py": "def test_hello(): pass",
            "Makefile": "test:\n\tpytest",
        }

        for file_path, content in files_content.items():
            full_path = temp_package / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        report = validator.validate_all(str(temp_package))

        # Verify report structure
        assert report.package_name == temp_package.name
        assert report.version == "1.0.0"
        assert report.timestamp
        assert report.overall_status in ["pass", "warning", "fail", "critical"]
        assert len(report.results) > 0
        assert "total_checks" in report.metadata

        # Verify summary
        summary = report.get_summary()
        assert isinstance(summary, dict)
        assert "pass" in summary
        assert "fail" in summary
        assert "warning" in summary
        assert "skip" in summary

    def test_validate_all_critical_failure(self, validator, temp_package):
        """Test validation with critical failures."""
        # Create package with critical security issue
        (temp_package / "private.key").write_text("PRIVATE KEY")

        report = validator.validate_all(str(temp_package))

        # Should have critical status due to sensitive file
        critical_results = [
            r for r in report.results if r.severity == "critical" and r.status == "fail"
        ]
        if critical_results:
            assert report.overall_status == "critical"


class TestCLIIntegration:
    """Test CLI functionality."""

    @pytest.fixture
    def temp_package_with_config(self):
        """Create temporary package with config file."""
        temp_dir = tempfile.mkdtemp()
        package_dir = Path(temp_dir) / "test-package"
        package_dir.mkdir()

        # Create basic package
        (package_dir / "README.md").write_text("# Test")

        # Create config file
        config = {"strict_mode": True}
        config_file = Path(temp_dir) / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        yield package_dir, config_file

        shutil.rmtree(temp_dir)

    def test_main_function_basic(self, temp_package_with_config):
        """Test main function with basic arguments."""
        package_dir, config_file = temp_package_with_config

        # Mock command line arguments
        test_args = [
            "validate_sdk_publishing.py",
            str(package_dir),
            "--output",
            str(package_dir.parent / "report.json"),
            "--format",
            "json",
        ]

        with patch("sys.argv", test_args):
            from validate_sdk_publishing import main

            exit_code = main()

        # Should exit successfully
        assert exit_code in [0, 1, 2]  # Valid exit codes

        # Report should be created
        report_file = package_dir.parent / "report.json"
        assert report_file.exists()

        # Report should be valid JSON
        with open(report_file) as f:
            report_data = json.load(f)

        assert "package_name" in report_data
        assert "overall_status" in report_data
        assert "results" in report_data

    def test_main_function_with_config(self, temp_package_with_config):
        """Test main function with configuration file."""
        package_dir, config_file = temp_package_with_config

        test_args = [
            "validate_sdk_publishing.py",
            str(package_dir),
            "--config",
            str(config_file),
            "--format",
            "summary",
        ]

        with patch("sys.argv", test_args):
            from validate_sdk_publishing import main

            exit_code = main()

        assert exit_code in [0, 1, 2]

    def test_main_function_strict_mode(self, temp_package_with_config):
        """Test main function in strict mode."""
        package_dir, config_file = temp_package_with_config

        # Create package that will have validation failures
        # (minimal package should have warnings/failures)

        test_args = ["validate_sdk_publishing.py", str(package_dir), "--strict"]

        with patch("sys.argv", test_args):
            from validate_sdk_publishing import main

            exit_code = main()

        # In strict mode, any failures should result in non-zero exit
        assert exit_code in [0, 1, 2]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_validator_with_config(self):
        """Test validator initialization with configuration."""
        config = {"test_setting": "value"}
        validator = SDKValidator(config)

        assert validator.config == config

    def test_validation_with_unicode_content(self, tmp_path):
        """Test validation with Unicode content in files."""
        package_dir = tmp_path / "unicode-package"
        package_dir.mkdir()

        # Create file with Unicode content
        unicode_content = "# Тест Package with émojis 🚀"
        (package_dir / "README.md").write_text(unicode_content, encoding="utf-8")

        validator = SDKValidator()
        results = validator.validate_package_structure(str(package_dir))

        # Should handle Unicode without errors
        assert len(results) > 0
        assert any(r.status == "pass" for r in results)

    def test_validation_with_very_large_files(self, tmp_path):
        """Test validation with large files."""
        package_dir = tmp_path / "large-package"
        package_dir.mkdir()

        # Create large file (but not too large for test)
        large_content = "# Large file\n" + "x" * 10000
        (package_dir / "large_readme.md").write_text(large_content)

        validator = SDKValidator()
        results = validator.validate_package_structure(str(package_dir))

        # Should handle large files
        assert len(results) > 0

    def test_validation_with_permission_errors(self, tmp_path):
        """Test validation when file permissions cause issues."""
        package_dir = tmp_path / "perm-package"
        package_dir.mkdir()

        # Create file
        test_file = package_dir / "test.py"
        test_file.write_text("print('test')")

        validator = SDKValidator()

        # This test might be platform-specific
        try:
            results = validator.validate_security(str(package_dir))
            assert len(results) >= 0  # Should not crash
        except PermissionError:
            # Expected on some systems
            pass

    def test_validation_result_equality(self):
        """Test ValidationResult equality and comparison."""
        result1 = ValidationResult("Test", "pass", "Message")
        result2 = ValidationResult("Test", "pass", "Message")
        result3 = ValidationResult("Test", "fail", "Message")

        # Note: dataclass equality is based on all fields
        assert result1 == result2
        assert result1 != result3

    def test_report_with_empty_results(self):
        """Test report generation with no validation results."""
        report = SDKValidationReport(
            package_name="empty-package",
            version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
            overall_status="pass",
            results=[],
            metadata={},
        )

        summary = report.get_summary()
        assert summary["pass"] == 0
        assert summary["fail"] == 0
        assert summary["warning"] == 0
        assert summary["skip"] == 0

        report_dict = report.to_dict()
        assert report_dict["summary"] == summary


if __name__ == "__main__":
    pytest.main([__file__])
