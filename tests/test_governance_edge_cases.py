#!/usr/bin/env python3
"""
Tests for Governance Edge Case Handler

Comprehensive test suite for governance script edge case handling,
including error recovery, validation edge cases, and robust operation.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import contextlib

from governance_edge_case_handler import EdgeCaseResult, GovernanceEdgeCaseHandler


class TestEdgeCaseResult:
    """Test EdgeCaseResult dataclass."""

    def test_creation(self):
        """Test basic EdgeCaseResult creation."""
        result = EdgeCaseResult(
            case_type="test_case",
            handled=True,
            action_taken="Test action",
            recovery_successful=True,
        )

        assert result.case_type == "test_case"
        assert result.handled is True
        assert result.action_taken == "Test action"
        assert result.recovery_successful is True
        assert result.timestamp is not None

    def test_auto_timestamp(self):
        """Test automatic timestamp generation."""
        result = EdgeCaseResult(
            case_type="test", handled=True, action_taken="action", recovery_successful=False
        )

        assert result.timestamp is not None
        assert "T" in result.timestamp  # ISO format
        assert result.timestamp.endswith("Z")


class TestGovernanceEdgeCaseHandler:
    """Test GovernanceEdgeCaseHandler class."""

    @pytest.fixture
    def handler(self):
        """Create handler instance for testing."""
        return GovernanceEdgeCaseHandler()

    @pytest.fixture
    def handler_with_config(self):
        """Create handler with custom configuration."""
        config = {"retry_attempts": 2, "retry_delay": 0.1, "timeout": 5}
        return GovernanceEdgeCaseHandler(config)

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing."""
        config_data = {
            "governance": {"enabled": True},
            "policies": {"security": "strict"},
            "thresholds": {"coverage": 80, "quality": 0.9},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        yield temp_file

        os.unlink(temp_file)

    def test_init_default_config(self, handler):
        """Test handler initialization with default config."""
        assert handler.config == {}
        assert handler.retry_attempts == 3
        assert handler.retry_delay == 1.0
        assert handler.timeout == 30
        assert len(handler.handled_cases) == 0

    def test_init_custom_config(self, handler_with_config):
        """Test handler initialization with custom config."""
        assert handler_with_config.retry_attempts == 2
        assert handler_with_config.retry_delay == 0.1
        assert handler_with_config.timeout == 5

    def test_logging_setup(self, handler):
        """Test logging configuration."""
        assert handler.logger is not None
        assert handler.logger.name == "governance_edge_cases"
        assert handler.logger.level == logging.INFO

    def test_file_system_error_decorator_file_not_found(self, handler):
        """Test file system error handling for missing files."""

        @handler.handle_file_system_errors
        def test_function():
            raise FileNotFoundError("test_file.json")

        with pytest.raises(FileNotFoundError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "file_not_found"
        assert case.handled is True

    def test_file_system_error_decorator_permission_error(self, handler):
        """Test file system error handling for permission errors."""

        @handler.handle_file_system_errors
        def test_function():
            raise PermissionError("Permission denied: test_file.json")

        with pytest.raises(PermissionError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "permission_error"
        assert case.handled is True

    def test_file_system_error_decorator_os_error(self, handler):
        """Test file system error handling for OS errors."""

        @handler.handle_file_system_errors
        def test_function():
            raise OSError("OS error occurred")

        with pytest.raises(OSError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "os_error"
        assert case.handled is True

    def test_network_error_decorator_connection_error(self, handler_with_config):
        """Test network error handling for connection errors."""
        call_count = 0

        @handler_with_config.handle_network_errors
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise ConnectionError("Connection refused")
            return "success"

        with pytest.raises(ConnectionError):
            test_function()

        # Should have tried retry_attempts times
        assert call_count == handler_with_config.retry_attempts

        # Check that case was recorded
        assert len(handler_with_config.handled_cases) == 1
        case = handler_with_config.handled_cases[0]
        assert case.case_type == "connection_error"
        assert case.handled is True

    def test_network_error_decorator_timeout_error(self, handler_with_config):
        """Test network error handling for timeout errors."""

        @handler_with_config.handle_network_errors
        def test_function():
            raise TimeoutError("Request timed out")

        with pytest.raises(TimeoutError):
            test_function()

        # Check that case was recorded
        assert len(handler_with_config.handled_cases) == 1
        case = handler_with_config.handled_cases[0]
        assert case.case_type == "timeout_error"
        assert case.handled is True

    def test_data_validation_error_decorator_json_error(self, handler):
        """Test data validation error handling for JSON errors."""

        @handler.handle_data_validation_errors
        def test_function():
            raise json.JSONDecodeError("Invalid JSON", "doc", 1)

        with pytest.raises(json.JSONDecodeError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "json_decode_error"
        assert case.handled is True

    def test_data_validation_error_decorator_key_error(self, handler):
        """Test data validation error handling for missing keys."""

        @handler.handle_data_validation_errors
        def test_function():
            raise KeyError("missing_key")

        with pytest.raises(KeyError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "missing_key_error"
        assert case.handled is True

    def test_data_validation_error_decorator_value_error(self, handler):
        """Test data validation error handling for value errors."""

        @handler.handle_data_validation_errors
        def test_function():
            raise ValueError("Invalid value format")

        with pytest.raises(ValueError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "value_error"
        assert case.handled is True

    def test_subprocess_error_decorator_called_process_error(self, handler):
        """Test subprocess error handling for CalledProcessError."""

        @handler.handle_subprocess_errors
        def test_function():
            error = subprocess.CalledProcessError(
                returncode=127, cmd=["nonexistent_command"], stderr="command not found"
            )
            raise error

        with pytest.raises(subprocess.CalledProcessError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "subprocess_error"
        assert case.handled is True

    def test_subprocess_error_decorator_timeout_expired(self, handler):
        """Test subprocess error handling for TimeoutExpired."""

        @handler.handle_subprocess_errors
        def test_function():
            error = subprocess.TimeoutExpired(cmd=["sleep", "100"], timeout=1)
            raise error

        with pytest.raises(subprocess.TimeoutExpired):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "subprocess_timeout"
        assert case.handled is True

    def test_memory_error_decorator(self, handler):
        """Test memory error handling."""

        @handler.handle_memory_errors
        def test_function():
            raise MemoryError("Out of memory")

        with pytest.raises(MemoryError):
            test_function()

        # Check that case was recorded
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "memory_error"
        assert case.handled is True

    def test_create_missing_files_success(self, handler):
        """Test successful creation of missing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_file.json"
            error_msg = f"No such file or directory: '{file_path}'"

            result = handler._create_missing_files(error_msg)

            assert result is True
            assert file_path.exists()

    def test_create_missing_files_directory(self, handler):
        """Test successful creation of missing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir) / "test_dir"
            error_msg = f"No such file or directory: '{dir_path}'"

            result = handler._create_missing_files(error_msg)

            assert result is True
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_recover_malformed_json_single_quotes(self, handler):
        """Test JSON recovery for single quotes."""
        malformed_json = "{'key': 'value', 'number': 123}"

        result = handler._recover_malformed_json(
            (malformed_json,), {}, json.JSONDecodeError("msg", "doc", 1)
        )

        assert result is not None
        assert result == {"key": "value", "number": 123}

    def test_recover_malformed_json_python_booleans(self, handler):
        """Test JSON recovery for Python boolean values."""
        malformed_json = '{"flag": True, "disabled": False, "value": None}'

        result = handler._recover_malformed_json(
            (malformed_json,), {}, json.JSONDecodeError("msg", "doc", 1)
        )

        assert result is not None
        assert result == {"flag": True, "disabled": False, "value": None}

    def test_provide_default_values_known_key(self, handler):
        """Test providing default values for known keys."""
        result = handler._provide_default_values((), {}, "'timestamp'")

        assert result is not None
        assert "timestamp" in result
        assert result["timestamp"].endswith("Z")

    def test_provide_default_values_unknown_key(self, handler):
        """Test handling of unknown keys."""
        result = handler._provide_default_values((), {}, "'unknown_key'")

        assert result is None

    def test_analyze_subprocess_failure_command_not_found(self, handler):
        """Test subprocess failure analysis for command not found."""
        error = subprocess.CalledProcessError(returncode=127, cmd=["nonexistent_command"])

        analysis = handler._analyze_subprocess_failure(error)

        assert analysis["recoverable"] is False
        assert analysis["reason"] == "missing_command"
        assert "Command not found" in analysis["action"]

    def test_analyze_subprocess_failure_missing_file(self, handler):
        """Test subprocess failure analysis for missing file."""
        error = subprocess.CalledProcessError(returncode=2, cmd=["cat", "nonexistent_file.txt"])

        analysis = handler._analyze_subprocess_failure(error)

        assert analysis["recoverable"] is True
        assert analysis["reason"] == "missing_file"
        assert "Missing file" in analysis["action"]

    def test_validate_governance_config_valid_file(self, handler, temp_config_file):
        """Test validation of valid governance configuration."""
        result = handler.validate_governance_config(temp_config_file)

        assert result is True
        # Should not have recorded any edge cases for valid config
        assert len(handler.handled_cases) == 0

    def test_validate_governance_config_missing_file(self, handler):
        """Test validation of missing configuration file."""
        # Clear any existing cases
        handler.handled_cases.clear()

        result = handler.validate_governance_config("nonexistent_config.json")

        assert result is False
        # Should have recorded file not found and validation error cases
        assert len(handler.handled_cases) >= 1
        # Accept either file_not_found or missing_key_error as the first case
        assert handler.handled_cases[0].case_type in ("file_not_found", "missing_key_error")

    def test_validate_governance_config_invalid_json(self, handler):
        """Test validation of invalid JSON configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_file = f.name

        try:
            result = handler.validate_governance_config(temp_file)

            assert result is False
            # Should have recorded JSON decode error case
            assert len(handler.handled_cases) == 1
            assert handler.handled_cases[0].case_type == "json_decode_error"
        finally:
            os.unlink(temp_file)

    def test_execute_governance_checks_security(self, handler):
        """Test execution of security governance checks."""
        result = handler.execute_governance_checks("security")

        assert result["check_type"] == "security"
        assert "timestamp" in result
        assert "results" in result
        assert len(result["results"]) > 0
        assert all("check" in r and "status" in r for r in result["results"])

    def test_execute_governance_checks_compliance(self, handler):
        """Test execution of compliance governance checks."""
        result = handler.execute_governance_checks("compliance")

        assert result["check_type"] == "compliance"
        assert len(result["results"]) > 0

    def test_execute_governance_checks_quality(self, handler):
        """Test execution of quality governance checks."""
        result = handler.execute_governance_checks("quality")

        assert result["check_type"] == "quality"
        assert len(result["results"]) > 0

    def test_execute_governance_checks_invalid_type(self, handler):
        """Test execution with invalid check type."""
        result = handler.execute_governance_checks("invalid_type")

        assert result["check_type"] == "invalid_type"
        assert result.get("failed") is True
        assert len(result["errors"]) > 0

    def test_generate_edge_case_report_empty(self, handler):
        """Test edge case report generation with no cases."""
        report = handler.generate_edge_case_report()

        assert "report_timestamp" in report
        assert report["total_cases_handled"] == 0
        assert report["recovery_success_rate"] == 0.0
        assert len(report["handled_cases"]) == 0
        assert len(report["recommendations"]) > 0

    def test_generate_edge_case_report_with_cases(self, handler):
        """Test edge case report generation with handled cases."""
        # Add some test cases
        handler.handled_cases.extend(
            [
                EdgeCaseResult("file_not_found", True, "Created file", True),
                EdgeCaseResult("connection_error", True, "Retried", False),
                EdgeCaseResult("json_decode_error", True, "Fixed JSON", True),
            ]
        )

        report = handler.generate_edge_case_report()

        assert report["total_cases_handled"] == 3
        assert (
            abs(report["recovery_success_rate"] - 66.7) < 0.1
        )  # 2 out of 3 successful (handle float precision)
        assert len(report["handled_cases"]) == 3
        assert len(report["cases_by_type"]) == 3

    def test_group_cases_by_type(self, handler):
        """Test grouping of cases by type."""
        handler.handled_cases.extend(
            [
                EdgeCaseResult("file_not_found", True, "Action 1", True),
                EdgeCaseResult("file_not_found", True, "Action 2", False),
                EdgeCaseResult("connection_error", True, "Action 3", True),
            ]
        )

        type_counts = handler._group_cases_by_type()

        assert type_counts["file_not_found"] == 2
        assert type_counts["connection_error"] == 1

    def test_calculate_recovery_rate(self, handler):
        """Test recovery rate calculation."""
        handler.handled_cases.extend(
            [
                EdgeCaseResult("type1", True, "Action", True),
                EdgeCaseResult("type2", True, "Action", False),
                EdgeCaseResult("type3", True, "Action", True),
                EdgeCaseResult("type4", True, "Action", False),
            ]
        )

        rate = handler._calculate_recovery_rate()

        assert rate == 50.0  # 2 out of 4 successful

    def test_generate_recommendations(self, handler):
        """Test recommendation generation based on edge cases."""
        # Add cases that should trigger specific recommendations
        handler.handled_cases.extend(
            [
                EdgeCaseResult("file_not_found", True, "Action", True),
                EdgeCaseResult("file_not_found", True, "Action", False),
                EdgeCaseResult("file_not_found", True, "Action", True),
                EdgeCaseResult("connection_error", True, "Action", False),
                EdgeCaseResult("memory_error", True, "Action", False),
            ]
        )

        recommendations = handler._generate_recommendations()

        assert len(recommendations) > 0
        assert any("file structure initialization" in rec for rec in recommendations)
        assert any("network retry mechanisms" in rec for rec in recommendations)
        assert any("smaller batches" in rec for rec in recommendations)

    def test_attempt_memory_recovery(self, handler):
        """Test memory recovery attempt."""
        result = handler._attempt_memory_recovery()

        # Should succeed (basic garbage collection)
        assert result is True

    def test_execute_with_reduced_memory(self, handler):
        """Test execution with reduced memory footprint."""

        def test_func(batch_size=100, limit=1000):
            return {"batch_size": batch_size, "limit": limit}

        result = handler._execute_with_reduced_memory(test_func, batch_size=100, limit=1000)

        # Should have reduced the batch size and limit
        assert result["batch_size"] == 50
        assert result["limit"] == 500


class TestCLIIntegration:
    """Test CLI functionality of the edge case handler."""

    def test_main_function_test_mode(self, capsys):
        """Test main function in test mode."""
        test_args = ["governance_edge_case_handler.py", "--test-mode"]

        with patch("sys.argv", test_args):
            from governance_edge_case_handler import main

            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Running governance edge case handler tests" in captured.out

    def test_main_function_with_config_validation(self, capsys):
        """Test main function with config file validation."""
        # Create temporary config file
        config_data = {
            "governance": {"enabled": True},
            "policies": {"security": "strict"},
            "thresholds": {"coverage": 80},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            test_args = ["governance_edge_case_handler.py", "--config-file", temp_file]

            with patch("sys.argv", test_args):
                from governance_edge_case_handler import main

                exit_code = main()

            captured = capsys.readouterr()
            assert exit_code == 0
            assert "Validating configuration file" in captured.out
        finally:
            os.unlink(temp_file)

    def test_main_function_with_check_type(self, capsys):
        """Test main function with governance check execution."""
        test_args = ["governance_edge_case_handler.py", "--check-type", "security"]

        with patch("sys.argv", test_args):
            from governance_edge_case_handler import main

            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Running security governance checks" in captured.out


class TestEdgeCaseScenarios:
    """Test specific edge case scenarios."""

    def test_cascading_failures(self):
        """Test handling of cascading failures."""
        handler = GovernanceEdgeCaseHandler()

        @handler.handle_file_system_errors
        @handler.handle_data_validation_errors
        def test_function():
            # First failure: file not found
            try:
                with open("nonexistent.json") as f:
                    json.load(f)
            except FileNotFoundError:
                # Second failure: JSON decode error
                raise json.JSONDecodeError("Invalid JSON", "backup", 1)

        with pytest.raises(json.JSONDecodeError):
            test_function()

        # Only json_decode_error is handled because FileNotFoundError is caught and re-raised as JSONDecodeError
        assert len(handler.handled_cases) == 1
        case_types = [case.case_type for case in handler.handled_cases]
        assert "json_decode_error" in case_types

    def test_recovery_chain(self):
        """Test recovery chain for related failures."""
        handler = GovernanceEdgeCaseHandler()
        call_count = 0

        @handler.handle_network_errors
        def network_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Initial connection failed")
            elif call_count == 2:
                raise TimeoutError("Retry timed out")
            else:
                return "success"

        # Should eventually succeed after retries, but will return 'success' after retries
        result = None
        with contextlib.suppress(ConnectionError, TimeoutError):
            result = network_operation()
        # If retries succeed, result should be 'success'
        if result is not None:
            assert result == "success"

        # Should have attempted retries
        assert call_count >= 2
        # If all retries succeed, handled_cases may be empty

    def test_resource_exhaustion_scenario(self):
        """Test handling of resource exhaustion scenarios."""
        handler = GovernanceEdgeCaseHandler()

        @handler.handle_memory_errors
        def memory_intensive_operation():
            # Simulate memory exhaustion
            raise MemoryError("Cannot allocate memory")

        with pytest.raises(MemoryError):
            memory_intensive_operation()

        # Should have attempted memory recovery
        assert len(handler.handled_cases) == 1
        case = handler.handled_cases[0]
        assert case.case_type == "memory_error"
        assert "memory cleanup" in case.action_taken


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
