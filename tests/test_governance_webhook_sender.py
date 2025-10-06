#!/usr/bin/env python3
"""Tests for governance webhook sender."""

import json
import os

# Add parent directory to path for imports
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.send_governance_webhook import (
    build_payload,
    determine_reasons,
    load_metrics,
    load_operations,
    sign_payload,
    validate_payload,
)


class TestGovernanceWebhook(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_load_metrics_missing_file(self):
        """Test loading metrics from non-existent file."""
        result = load_metrics("/nonexistent/path")
        expected = {"window_stability_ratio": 0.0, "breaking": True, "score": 0}
        self.assertEqual(result, expected)

    def test_load_metrics_valid_file(self):
        """Test loading metrics from valid JSON file."""
        metrics_data = {
            "window_stability_ratio": 0.95,
            "breaking": False,
            "score": 88,
            "current_stable_streak": 5,
        }

        metrics_file = os.path.join(self.temp_dir, "metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(metrics_data, f)

        result = load_metrics(metrics_file)
        self.assertEqual(result, metrics_data)

    def test_load_operations_missing_file(self):
        """Test loading operations from non-existent file."""
        result = load_operations("/nonexistent/path")
        expected = {"added": 0, "removed": 0}
        self.assertEqual(result, expected)

    def test_load_operations_valid_file(self):
        """Test loading operations from valid JSON file."""
        operations_data = {
            "added": [
                {"path": "/api/v1/new-endpoint", "method": "POST"},
                {"path": "/api/v1/another", "method": "GET"},
            ],
            "removed": [{"path": "/api/v1/old-endpoint", "method": "DELETE"}],
        }

        ops_file = os.path.join(self.temp_dir, "operations.json")
        with open(ops_file, "w") as f:
            json.dump(operations_data, f)

        result = load_operations(ops_file)
        expected = {"added": 2, "removed": 1}
        self.assertEqual(result, expected)

    def test_determine_reasons_failure_cases(self):
        """Test reason determination for failure scenarios."""
        # Semver failure
        metrics = {"window_stability_ratio": 0.9, "current_stable_streak": 0}
        reasons = determine_reasons(metrics, "fail")
        self.assertIn("semver_fail", reasons)

        # Stability drop
        metrics = {"window_stability_ratio": 0.5, "current_stable_streak": 0}
        reasons = determine_reasons(metrics, "ok")
        self.assertIn("stability_drop", reasons)

        # Placeholder streak
        metrics = {
            "window_stability_ratio": 0.9,
            "current_stable_streak": 0,
            "extensions": {"placeholder_streak": 5},
        }
        reasons = determine_reasons(metrics, "ok")
        self.assertIn("placeholder_streak", reasons)

    def test_determine_reasons_recovery_cases(self):
        """Test reason determination for recovery scenarios."""
        metrics = {
            "window_stability_ratio": 0.9,
            "current_stable_streak": 3,
            "extensions": {"placeholder_streak": 0},
        }
        reasons = determine_reasons(metrics, "ok")

        self.assertIn("stability_recovered", reasons)
        self.assertIn("placeholder_recovered", reasons)
        self.assertIn("semver_recovered", reasons)

    def test_build_payload_structure(self):
        """Test payload structure and content."""
        metrics = {
            "window_stability_ratio": 0.95,
            "current_stable_streak": 5,
            "score": 88,
            "timestamp": "2025-10-03T12:00:00Z",
            "window_size": 30,
        }
        operations = {"added": 2, "removed": 1}

        with patch("scripts.send_governance_webhook.get_git_sha", return_value="abc12345"):
            payload = build_payload(metrics, operations, "ok")

        # Check required fields
        self.assertEqual(payload["event"], "governance_notice")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["sha"], "abc12345")
        self.assertEqual(payload["semver_status"], "ok")
        self.assertEqual(payload["stability_ratio"], 0.95)
        self.assertIsInstance(payload["reasons"], list)

        # Check operations structure
        self.assertEqual(payload["operations"]["added"], 2)
        self.assertEqual(payload["operations"]["removed"], 1)

        # Check metadata
        self.assertIn("metadata", payload)
        self.assertEqual(payload["metadata"]["score"], 88)

    def test_validate_payload_valid(self):
        """Test payload validation with valid payload."""
        payload = {
            "event": "governance_notice",
            "version": 1,
            "sha": "abc12345",
            "semver_status": "ok",
            "stability_ratio": 0.95,
            "reasons": ["stability_recovered"],
            "operations": {"added": 1, "removed": 0},
        }

        self.assertTrue(validate_payload(payload))

    def test_validate_payload_missing_fields(self):
        """Test payload validation with missing required fields."""
        payload = {
            "event": "governance_notice",
            "version": 1,
            # Missing sha, semver_status, etc.
        }

        self.assertFalse(validate_payload(payload))

    def test_validate_payload_invalid_semver_status(self):
        """Test payload validation with invalid semver status."""
        payload = {
            "event": "governance_notice",
            "version": 1,
            "sha": "abc12345",
            "semver_status": "invalid_status",
            "stability_ratio": 0.95,
            "reasons": [],
            "operations": {"added": 1, "removed": 0},
        }

        self.assertFalse(validate_payload(payload))

    def test_validate_payload_negative_operations(self):
        """Test payload validation with negative operation counts."""
        payload = {
            "event": "governance_notice",
            "version": 1,
            "sha": "abc12345",
            "semver_status": "ok",
            "stability_ratio": 0.95,
            "reasons": [],
            "operations": {"added": -1, "removed": 0},
        }

        self.assertFalse(validate_payload(payload))

    def test_validate_payload_invalid_reasons(self):
        """Test payload validation with invalid reason codes."""
        payload = {
            "event": "governance_notice",
            "version": 1,
            "sha": "abc12345",
            "semver_status": "ok",
            "stability_ratio": 0.95,
            "reasons": ["invalid_reason", "another_invalid"],
            "operations": {"added": 1, "removed": 0},
        }

        self.assertFalse(validate_payload(payload))

    def test_sign_payload(self):
        """Test HMAC signature generation."""
        payload_bytes = b'{"test": "data"}'
        secret = "test_secret_key"

        signature = sign_payload(payload_bytes, secret)

        self.assertTrue(signature.startswith("sha256="))
        self.assertEqual(len(signature), 71)  # "sha256=" + 64 hex chars

    def test_sign_payload_empty_secret(self):
        """Test signature generation with empty secret."""
        payload_bytes = b'{"test": "data"}'
        secret = ""

        signature = sign_payload(payload_bytes, secret)
        self.assertEqual(signature, "")

    def test_edge_case_reasons_deduplication(self):
        """Test that duplicate reasons are removed."""
        metrics = {
            "window_stability_ratio": 0.9,
            "current_stable_streak": 3,
            "extensions": {"placeholder_streak": 0},
        }

        # This should generate recovery reasons, but they should be deduplicated
        reasons = determine_reasons(metrics, "ok")

        # Check no duplicates
        self.assertEqual(len(reasons), len(set(reasons)))

    def test_stability_ratio_edge_cases(self):
        """Test stability ratio edge cases (exactly at thresholds)."""
        # Exactly at threshold (0.7)
        metrics = {"window_stability_ratio": 0.7, "current_stable_streak": 0}
        reasons = determine_reasons(metrics, "ok")
        self.assertNotIn("stability_drop", reasons)

        # Just below threshold
        metrics = {"window_stability_ratio": 0.69, "current_stable_streak": 0}
        reasons = determine_reasons(metrics, "ok")
        self.assertIn("stability_drop", reasons)

    def test_operations_malformed_json(self):
        """Test handling of malformed operations JSON."""
        ops_file = os.path.join(self.temp_dir, "bad_operations.json")
        with open(ops_file, "w") as f:
            f.write('{"invalid": json}')  # Malformed JSON

        result = load_operations(ops_file)
        expected = {"added": 0, "removed": 0}
        self.assertEqual(result, expected)


class TestWebhookIntegration(unittest.TestCase):
    """Integration tests for webhook sending functionality."""

    @patch("urllib.request.urlopen")
    def test_webhook_success_response(self, mock_urlopen):
        """Test successful webhook delivery."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from scripts.send_governance_webhook import send_webhook

        payload = {
            "event": "governance_notice",
            "version": 1,
            "sha": "abc12345",
            "semver_status": "ok",
            "stability_ratio": 0.95,
            "reasons": [],
            "operations": {"added": 1, "removed": 0},
        }

        result = send_webhook("https://example.com/webhook", payload)
        self.assertTrue(result)

    @patch("urllib.request.urlopen")
    def test_webhook_http_error(self, mock_urlopen):
        """Test webhook delivery with HTTP error."""
        import io
        from urllib.error import HTTPError

        # Mock HTTP error response
        mock_urlopen.side_effect = HTTPError(
            url="https://example.com/webhook",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.StringIO('{"error": "Invalid payload"}'),
        )

        from scripts.send_governance_webhook import send_webhook

        payload = {"test": "data"}
        result = send_webhook("https://example.com/webhook", payload)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
