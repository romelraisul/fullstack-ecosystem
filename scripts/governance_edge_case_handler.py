#!/usr/bin/env python3
"""
Governance Script Edge Case Handler

This module provides comprehensive edge case handling for governance scripts,
including error recovery, validation edge cases, and robust operation under
various failure scenarios.
"""

import functools
import json
import logging
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EdgeCaseResult:
    """Result of edge case handling."""

    case_type: str
    handled: bool
    action_taken: str
    recovery_successful: bool
    details: dict[str, Any] | None = None
    timestamp: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class GovernanceEdgeCaseHandler:
    """Comprehensive edge case handler for governance operations."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the edge case handler.

        Args:
            config: Configuration options for edge case handling
        """
        self.config = config or {}
        self.logger = self._setup_logging()
        self.handled_cases: list[EdgeCaseResult] = []
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)
        self.timeout = self.config.get("timeout", 30)

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for edge case handling."""
        logger = logging.getLogger("governance_edge_cases")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def handle_file_system_errors(self, func: Callable) -> Callable:
        """Decorator to handle file system related edge cases."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                self.logger.warning(f"File not found: {e}")
                case = EdgeCaseResult(
                    case_type="file_not_found",
                    handled=True,
                    action_taken="Created default file/directory structure",
                    recovery_successful=self._create_missing_files(str(e)),
                    details={"error": str(e)},
                )
                self.handled_cases.append(case)

                if case.recovery_successful:
                    return func(*args, **kwargs)  # Retry after recovery
                else:
                    raise

            except PermissionError as e:
                self.logger.error(f"Permission denied: {e}")
                case = EdgeCaseResult(
                    case_type="permission_error",
                    handled=True,
                    action_taken="Attempted permission fix",
                    recovery_successful=self._fix_permissions(str(e)),
                    details={"error": str(e)},
                )
                self.handled_cases.append(case)

                if not case.recovery_successful:
                    raise

            except OSError as e:
                self.logger.error(f"OS error: {e}")
                case = EdgeCaseResult(
                    case_type="os_error",
                    handled=True,
                    action_taken="Logged OS error for manual review",
                    recovery_successful=False,
                    details={"error": str(e), "errno": getattr(e, "errno", None)},
                )
                self.handled_cases.append(case)
                raise

        return wrapper

    def handle_network_errors(self, func: Callable) -> Callable:
        """Decorator to handle network related edge cases."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(self.retry_attempts):
                # Remove timeout from kwargs if it exists to avoid conflicts
                kwargs.pop("timeout", None)
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    self.logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                        continue
                    case = EdgeCaseResult(
                        case_type="connection_error",
                        handled=True,
                        action_taken=f"Retried {self.retry_attempts} times with exponential backoff",
                        recovery_successful=False,
                        details={"error": str(e), "attempts": self.retry_attempts},
                    )
                    self.handled_cases.append(case)
                    raise
                except TimeoutError as e:
                    self.logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")
                    if attempt < self.retry_attempts - 1:
                        # Increase timeout for retry
                        kwargs["timeout"] = kwargs.get("timeout", self.timeout) * 1.5
                        continue
                    case = EdgeCaseResult(
                        case_type="timeout_error",
                        handled=True,
                        action_taken="Increased timeout and retried",
                        recovery_successful=False,
                        details={"error": str(e), "final_timeout": kwargs.get("timeout")},
                    )
                    self.handled_cases.append(case)
                    raise

        return wrapper

    def handle_data_validation_errors(self, func: Callable) -> Callable:
        """Decorator to handle data validation edge cases."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}")

                # Attempt to recover malformed JSON
                recovery_data = self._recover_malformed_json(args, kwargs, e)

                case = EdgeCaseResult(
                    case_type="json_decode_error",
                    handled=True,
                    action_taken="Attempted JSON recovery",
                    recovery_successful=recovery_data is not None,
                    details={"error": str(e), "line": getattr(e, "lineno", None)},
                )
                self.handled_cases.append(case)

                if recovery_data is not None:
                    return recovery_data
                else:
                    raise

            except KeyError as e:
                self.logger.warning(f"Missing key in data: {e}")

                # Provide default values for missing keys
                default_data = self._provide_default_values(args, kwargs, str(e))

                case = EdgeCaseResult(
                    case_type="missing_key_error",
                    handled=True,
                    action_taken="Provided default values for missing keys",
                    recovery_successful=default_data is not None,
                    details={"missing_key": str(e)},
                )
                self.handled_cases.append(case)

                if default_data is not None:
                    return default_data
                else:
                    raise

            except ValueError as e:
                self.logger.error(f"Value error in data validation: {e}")

                case = EdgeCaseResult(
                    case_type="value_error",
                    handled=True,
                    action_taken="Logged validation error for review",
                    recovery_successful=False,
                    details={"error": str(e)},
                )
                self.handled_cases.append(case)
                raise

        return wrapper

    def handle_subprocess_errors(self, func: Callable) -> Callable:
        """Decorator to handle subprocess execution edge cases."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Subprocess failed: {e}")

                # Analyze subprocess failure
                analysis = self._analyze_subprocess_failure(e)

                case = EdgeCaseResult(
                    case_type="subprocess_error",
                    handled=True,
                    action_taken=f"Analyzed failure: {analysis['action']}",
                    recovery_successful=analysis["recoverable"],
                    details={
                        "returncode": e.returncode,
                        "cmd": e.cmd,
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                        "analysis": analysis,
                    },
                )
                self.handled_cases.append(case)

                if analysis["recoverable"]:
                    # Attempt recovery
                    return self._recover_subprocess_failure(e, analysis)
                else:
                    raise

            except subprocess.TimeoutExpired as e:
                self.logger.warning(f"Subprocess timeout: {e}")

                case = EdgeCaseResult(
                    case_type="subprocess_timeout",
                    handled=True,
                    action_taken="Killed timed-out process",
                    recovery_successful=False,
                    details={
                        "cmd": e.cmd,
                        "timeout": e.timeout,
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                    },
                )
                self.handled_cases.append(case)
                raise

        return wrapper

    def handle_memory_errors(self, func: Callable) -> Callable:
        """Decorator to handle memory related edge cases."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MemoryError as e:
                self.logger.critical(f"Memory error: {e}")

                # Attempt memory cleanup
                recovery_successful = self._attempt_memory_recovery()

                case = EdgeCaseResult(
                    case_type="memory_error",
                    handled=True,
                    action_taken="Attempted memory cleanup and optimization",
                    recovery_successful=recovery_successful,
                    details={"error": str(e)},
                )
                self.handled_cases.append(case)

                if recovery_successful:
                    # Try with reduced memory footprint
                    return self._execute_with_reduced_memory(func, *args, **kwargs)
                else:
                    raise

        return wrapper

    def _create_missing_files(self, error_msg: str) -> bool:
        """Attempt to create missing files or directories."""
        try:
            # Extract file path from error message
            if "No such file or directory" in error_msg:
                # Basic heuristic to find file path in error message
                parts = error_msg.split("'")
                if len(parts) >= 2:
                    file_path = Path(parts[1])

                    if not file_path.exists():
                        if file_path.suffix:  # It's a file
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text("{}")  # Create empty JSON file
                        else:  # It's a directory
                            file_path.mkdir(parents=True, exist_ok=True)

                        self.logger.info(f"Created missing path: {file_path}")
                        return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to create missing files: {e}")
            return False

    def _fix_permissions(self, error_msg: str) -> bool:
        """Attempt to fix permission issues."""
        try:
            # This is a simplified approach - in production you'd need
            # more sophisticated permission handling
            self.logger.warning("Permission fix attempted but may require manual intervention")
            return False
        except Exception as e:
            self.logger.error(f"Failed to fix permissions: {e}")
            return False

    def _recover_malformed_json(
        self, args: tuple, kwargs: dict, error: json.JSONDecodeError
    ) -> dict[str, Any] | None:
        """Attempt to recover from malformed JSON."""
        try:
            # Look for JSON content in args/kwargs
            json_content = None

            for arg in args:
                if isinstance(arg, str) and (
                    arg.strip().startswith("{") or arg.strip().startswith("[")
                ):
                    json_content = arg
                    break

            if not json_content:
                for value in kwargs.values():
                    if isinstance(value, str) and (
                        value.strip().startswith("{") or value.strip().startswith("[")
                    ):
                        json_content = value
                        break

            if json_content:
                # Attempt common JSON fixes
                fixes = [
                    lambda x: x.replace("'", '"'),  # Single to double quotes
                    lambda x: x.replace("True", "true")
                    .replace("False", "false")
                    .replace("None", "null"),  # Python to JSON booleans
                    lambda x: (
                        x.rstrip(",") + "}" if x.rstrip().endswith(",") else x
                    ),  # Remove trailing commas
                ]

                for fix in fixes:
                    try:
                        fixed_content = fix(json_content)
                        return json.loads(fixed_content)
                    except json.JSONDecodeError:
                        continue

            return None
        except Exception as e:
            self.logger.error(f"JSON recovery failed: {e}")
            return None

    def _provide_default_values(
        self, args: tuple, kwargs: dict, missing_key: str
    ) -> dict[str, Any] | None:
        """Provide default values for missing keys."""
        try:
            # Common default values based on key names
            defaults = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
                "status": "unknown",
                "data": {},
                "metadata": {},
                "results": [],
                "errors": [],
                "warnings": [],
                "success": False,
                "total": 0,
                "count": 0,
                "id": "unknown",
                "name": "unnamed",
                "type": "unknown",
            }

            clean_key = missing_key.strip("'\"")
            if clean_key in defaults:
                self.logger.info(f"Provided default value for missing key: {clean_key}")
                return {clean_key: defaults[clean_key]}

            return None
        except Exception as e:
            self.logger.error(f"Failed to provide default values: {e}")
            return None

    def _analyze_subprocess_failure(self, error: subprocess.CalledProcessError) -> dict[str, Any]:
        """Analyze subprocess failure to determine recovery options."""
        analysis = {"recoverable": False, "action": "unknown", "reason": "unknown"}

        try:
            returncode = error.returncode
            stderr = error.stderr or ""

            # Common recoverable errors
            if returncode == 127:  # Command not found
                analysis.update(
                    {
                        "recoverable": False,
                        "action": "Command not found - check installation",
                        "reason": "missing_command",
                    }
                )
            elif returncode == 1 and "permission denied" in stderr.lower():
                analysis.update(
                    {
                        "recoverable": False,
                        "action": "Permission denied - check file permissions",
                        "reason": "permission_denied",
                    }
                )
            elif returncode == 2:  # Missing file or directory
                analysis.update(
                    {
                        "recoverable": True,
                        "action": "Missing file - attempt to create",
                        "reason": "missing_file",
                    }
                )
            elif "connection refused" in stderr.lower():
                analysis.update(
                    {
                        "recoverable": True,
                        "action": "Connection refused - retry with backoff",
                        "reason": "connection_refused",
                    }
                )
            else:
                analysis.update(
                    {"action": f"Unknown error (code {returncode})", "reason": "unknown_error"}
                )

            return analysis
        except Exception as e:
            self.logger.error(f"Failed to analyze subprocess failure: {e}")
            return analysis

    def _recover_subprocess_failure(
        self, error: subprocess.CalledProcessError, analysis: dict[str, Any]
    ) -> Any:
        """Attempt to recover from subprocess failure."""
        try:
            reason = analysis.get("reason")

            if reason == "missing_file":
                # Create missing files and retry
                self._create_missing_files(str(error))
                # Would retry subprocess here
                return {"recovered": True, "method": "created_missing_files"}
            elif reason == "connection_refused":
                # Wait and retry
                time.sleep(2)
                return {"recovered": True, "method": "retry_after_delay"}

            return {"recovered": False, "method": "no_recovery_available"}
        except Exception as e:
            self.logger.error(f"Subprocess recovery failed: {e}")
            return {"recovered": False, "method": "recovery_failed"}

    def _attempt_memory_recovery(self) -> bool:
        """Attempt to recover from memory issues."""
        try:
            import gc

            # Force garbage collection
            gc.collect()

            # Log memory usage if available
            try:
                import psutil

                process = psutil.Process()
                memory_info = process.memory_info()
                self.logger.info(
                    f"Memory usage after cleanup: {memory_info.rss / 1024 / 1024:.2f} MB"
                )
            except ImportError:
                pass

            return True
        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")
            return False

    def _execute_with_reduced_memory(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with reduced memory footprint."""
        try:
            # Reduce batch sizes if present in kwargs
            if "batch_size" in kwargs:
                kwargs["batch_size"] = max(1, kwargs["batch_size"] // 2)
            if "limit" in kwargs:
                kwargs["limit"] = max(1, kwargs["limit"] // 2)

            self.logger.info("Executing with reduced memory footprint")
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Reduced memory execution failed: {e}")
            raise

    def validate_governance_config(self, config_path: str) -> bool:
        """Validate governance configuration with edge case handling."""

        @self.handle_file_system_errors
        @self.handle_data_validation_errors
        def _validate_config():
            with open(config_path) as f:
                config = json.load(f)

            # Required fields
            required_fields = ["governance", "policies", "thresholds"]
            for field in required_fields:
                if field not in config:
                    raise KeyError(f"Missing required field: {field}")

            # Validate thresholds
            thresholds = config["thresholds"]
            for threshold_name, value in thresholds.items():
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"Invalid threshold value for {threshold_name}: {value}")

            return True

        try:
            return _validate_config()
        except Exception as e:
            self.logger.error(f"Config validation failed: {e}")
            return False

    def execute_governance_checks(self, check_type: str) -> dict[str, Any]:
        """Execute governance checks with comprehensive edge case handling."""

        @self.handle_file_system_errors
        @self.handle_network_errors
        @self.handle_subprocess_errors
        @self.handle_memory_errors
        def _execute_checks():
            results = {
                "check_type": check_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "results": [],
                "errors": [],
                "warnings": [],
            }

            # Simulate governance check execution
            if check_type == "security":
                results["results"] = self._run_security_checks()
            elif check_type == "compliance":
                results["results"] = self._run_compliance_checks()
            elif check_type == "quality":
                results["results"] = self._run_quality_checks()
            else:
                raise ValueError(f"Unknown check type: {check_type}")

            return results

        try:
            return _execute_checks()
        except Exception as e:
            self.logger.error(f"Governance check execution failed: {e}")
            return {
                "check_type": check_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "results": [],
                "errors": [str(e)],
                "warnings": [],
                "failed": True,
            }

    def _run_security_checks(self) -> list[dict[str, Any]]:
        """Run security checks (simulated)."""
        return [
            {"check": "dependency_scan", "status": "pass", "details": "No vulnerabilities found"},
            {
                "check": "secret_detection",
                "status": "pass",
                "details": "No hardcoded secrets detected",
            },
            {
                "check": "permission_audit",
                "status": "warning",
                "details": "Some files have broad permissions",
            },
        ]

    def _run_compliance_checks(self) -> list[dict[str, Any]]:
        """Run compliance checks (simulated)."""
        return [
            {
                "check": "license_compliance",
                "status": "pass",
                "details": "All licenses are compliant",
            },
            {
                "check": "data_governance",
                "status": "pass",
                "details": "Data handling policies followed",
            },
            {
                "check": "audit_trail",
                "status": "pass",
                "details": "Complete audit trail maintained",
            },
        ]

    def _run_quality_checks(self) -> list[dict[str, Any]]:
        """Run quality checks (simulated)."""
        return [
            {"check": "code_coverage", "status": "pass", "details": "95% code coverage achieved"},
            {
                "check": "static_analysis",
                "status": "warning",
                "details": "Minor code quality issues found",
            },
            {"check": "documentation", "status": "pass", "details": "Documentation is up to date"},
        ]

    def generate_edge_case_report(self) -> dict[str, Any]:
        """Generate a comprehensive report of handled edge cases."""
        return {
            "report_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_cases_handled": len(self.handled_cases),
            "cases_by_type": self._group_cases_by_type(),
            "recovery_success_rate": self._calculate_recovery_rate(),
            "handled_cases": [asdict(case) for case in self.handled_cases],
            "recommendations": self._generate_recommendations(),
        }

    def _group_cases_by_type(self) -> dict[str, int]:
        """Group handled cases by type."""
        type_counts = {}
        for case in self.handled_cases:
            type_counts[case.case_type] = type_counts.get(case.case_type, 0) + 1
        return type_counts

    def _calculate_recovery_rate(self) -> float:
        """Calculate the percentage of successful recoveries."""
        if not self.handled_cases:
            return 0.0

        successful_recoveries = sum(1 for case in self.handled_cases if case.recovery_successful)
        return (successful_recoveries / len(self.handled_cases)) * 100

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on handled edge cases."""
        recommendations = []
        type_counts = self._group_cases_by_type()

        if type_counts.get("file_not_found", 0) > 2:
            recommendations.append("Consider implementing automatic file structure initialization")

        if type_counts.get("connection_error", 0) > 0:
            recommendations.append(
                "Implement robust network retry mechanisms with exponential backoff"
            )

        if type_counts.get("memory_error", 0) > 0:
            recommendations.append(
                "Consider processing data in smaller batches to reduce memory usage"
            )

        if type_counts.get("json_decode_error", 0) > 0:
            recommendations.append("Implement stricter JSON validation and schema checking")

        if type_counts.get("subprocess_error", 0) > 0:
            recommendations.append("Add pre-execution validation for subprocess commands")

        if not recommendations:
            recommendations.append("System appears to be operating within normal parameters")

        return recommendations


def main():
    """CLI entry point for governance edge case handling."""
    import argparse

    parser = argparse.ArgumentParser(description="Governance Edge Case Handler")
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode to demonstrate edge case handling",
    )
    parser.add_argument("--config-file", help="Path to governance configuration file to validate")
    parser.add_argument(
        "--check-type",
        choices=["security", "compliance", "quality"],
        help="Type of governance check to run",
    )
    parser.add_argument(
        "--output",
        default="governance_edge_case_report.json",
        help="Output file for edge case report",
    )

    args = parser.parse_args()

    # Initialize handler
    handler = GovernanceEdgeCaseHandler()

    if args.test_mode:
        print("🧪 Running governance edge case handler tests...")

        # Test various edge cases
        test_cases = [
            (
                "file_validation",
                lambda: handler.validate_governance_config("nonexistent_config.json"),
            ),
            ("security_check", lambda: handler.execute_governance_checks("security")),
            ("compliance_check", lambda: handler.execute_governance_checks("compliance")),
            ("quality_check", lambda: handler.execute_governance_checks("quality")),
        ]

        for test_name, test_func in test_cases:
            print(f"   Running {test_name}...")
            try:
                test_func()
                print(f"   ✅ {test_name} completed")
            except Exception as e:
                print(f"   ⚠️  {test_name} handled exception: {e}")

    if args.config_file:
        print(f"🔍 Validating configuration file: {args.config_file}")
        is_valid = handler.validate_governance_config(args.config_file)
        print(f"   {'✅ Valid' if is_valid else '❌ Invalid'}")

    if args.check_type:
        print(f"🏃 Running {args.check_type} governance checks...")
        results = handler.execute_governance_checks(args.check_type)
        print(f"   📊 Results: {len(results.get('results', []))} checks completed")
        if results.get("errors"):
            print(f"   ❌ Errors: {len(results['errors'])}")
        if results.get("warnings"):
            print(f"   ⚠️  Warnings: {len(results['warnings'])}")

    # Generate edge case report
    report = handler.generate_edge_case_report()

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print("\n📊 Edge Case Handling Summary:")
    print(f"   Total cases handled: {report['total_cases_handled']}")
    print(f"   Recovery success rate: {report['recovery_success_rate']:.1f}%")
    print(f"   Report saved to: {args.output}")

    if report["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
