#!/usr/bin/env python3
"""Send governance webhook notifications for semver status and stability changes.

This script is designed to be called by CI/CD workflows to notify external systems
about governance status changes, API stability metrics, and recovery events.

Usage:
  python scripts/send_governance_webhook.py --metrics stability-metrics.json --operations operations-classification.json

Environment variables:
  GOVERNANCE_WEBHOOK_URL - Target webhook URL (required)
  GOVERNANCE_WEBHOOK_SECRET - Optional HMAC signing secret
  SEMVER_STATUS - Override semver status (ok|warn|fail|unknown)

Exit codes:
  0 - Success
  1 - Configuration error
  2 - Webhook delivery failure
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def load_metrics(path: str) -> dict[str, Any]:
    """Load stability metrics JSON file."""
    if not os.path.exists(path):
        return {"window_stability_ratio": 0.0, "breaking": True, "score": 0}

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_operations(path: str) -> dict[str, int]:
    """Load operations classification and count changes."""
    if not os.path.exists(path):
        return {"added": 0, "removed": 0}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Count operations by type
        added = len(data.get("added", []))
        removed = len(data.get("removed", []))

        return {"added": added, "removed": removed}
    except Exception:
        return {"added": 0, "removed": 0}


def determine_reasons(metrics: dict[str, Any], semver_status: str) -> list[str]:
    """Determine failure and recovery reasons based on current state."""
    reasons = []

    # Check for failures
    if semver_status == "fail":
        reasons.append("semver_fail")

    # Check stability ratio (threshold: < 0.7 = stability drop)
    stability_ratio = metrics.get("window_stability_ratio", 1.0)
    if stability_ratio < 0.7:
        reasons.append("stability_drop")

    # Check for placeholder streak (if extensions indicate metrics issues)
    placeholder_streak = metrics.get("extensions", {}).get("placeholder_streak", 0)
    if placeholder_streak >= 3:
        reasons.append("placeholder_streak")

    # Check for recovery conditions
    # Recovery is detected by good current state + recent improvement
    current_stable_streak = metrics.get("current_stable_streak", 0)

    if semver_status == "ok" and current_stable_streak >= 2:
        # Only add recovery if we previously had issues
        if stability_ratio >= 0.8:  # Recovered stability
            reasons.append("stability_recovered")
        if placeholder_streak == 0:  # No longer in placeholder state
            reasons.append("placeholder_recovered")
        # Semver recovery is implied by ok status after previous issues
        reasons.append("semver_recovered")

    return list(set(reasons))  # Remove duplicates


def get_git_sha() -> str:
    """Get current git commit SHA."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()[:8]  # Short SHA
    except Exception:
        return "unknown"


def build_payload(
    metrics: dict[str, Any], operations: dict[str, int], semver_status: str
) -> dict[str, Any]:
    """Build the governance webhook payload according to schema."""
    reasons = determine_reasons(metrics, semver_status)
    stability_ratio = metrics.get("window_stability_ratio", 0.0)

    payload = {
        "event": "governance_notice",
        "version": 1,
        "sha": get_git_sha(),
        "semver_status": semver_status,
        "stability_ratio": round(stability_ratio, 4),
        "reasons": reasons,
        "operations": {
            "added": operations.get("added", 0),
            "removed": operations.get("removed", 0),
        },
    }

    # Add optional metadata for debugging
    payload["metadata"] = {
        "timestamp": metrics.get("timestamp", "unknown"),
        "current_stable_streak": metrics.get("current_stable_streak", 0),
        "window_size": metrics.get("window_size", 0),
        "score": metrics.get("score", 0),
    }

    return payload


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Create HMAC-SHA256 signature for payload."""
    if not secret:
        return ""

    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    return f"sha256={signature}"


def send_webhook(url: str, payload: dict[str, Any], secret: str = "") -> bool:
    """Send webhook payload to target URL."""
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "governance-webhook-sender/1.0",
        "X-Governance-Event": "governance_notice",
    }

    # Add signature if secret provided
    if secret:
        signature = sign_payload(payload_bytes, secret)
        headers["X-Hub-Signature-256"] = signature

    try:
        request = urllib.request.Request(url, data=payload_bytes, headers=headers)

        with urllib.request.urlopen(request, timeout=30) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")

            if 200 <= status_code < 300:
                print(f"✅ Webhook sent successfully (HTTP {status_code})")
                return True
            else:
                print(f"⚠️ Unexpected response (HTTP {status_code}): {response_body}")
                return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "No details"
        print(f"❌ HTTP Error {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def validate_payload(payload: dict[str, Any]) -> bool:
    """Validate payload against schema requirements."""
    required_fields = [
        "event",
        "version",
        "sha",
        "semver_status",
        "stability_ratio",
        "reasons",
        "operations",
    ]

    for field in required_fields:
        if field not in payload:
            print(f"❌ Missing required field: {field}")
            return False

    # Validate semver_status enum
    if payload["semver_status"] not in ["ok", "warn", "fail", "unknown"]:
        print(f"❌ Invalid semver_status: {payload['semver_status']}")
        return False

    # Validate operations structure
    ops = payload["operations"]
    if not isinstance(ops, dict) or "added" not in ops or "removed" not in ops:
        print("❌ Invalid operations structure")
        return False

    if not isinstance(ops["added"], int) or not isinstance(ops["removed"], int):
        print("❌ Operations counts must be integers")
        return False

    if ops["added"] < 0 or ops["removed"] < 0:
        print("❌ Operations counts must be non-negative")
        return False

    # Validate reasons
    valid_reasons = [
        "semver_fail",
        "stability_drop",
        "placeholder_streak",
        "semver_recovered",
        "stability_recovered",
        "placeholder_recovered",
    ]

    for reason in payload["reasons"]:
        if reason not in valid_reasons:
            print(f"❌ Invalid reason: {reason}")
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Send governance webhook notifications")
    parser.add_argument(
        "--metrics", default="stability-metrics.json", help="Path to stability metrics JSON file"
    )
    parser.add_argument(
        "--operations",
        default="operations-classification.json",
        help="Path to operations classification JSON file",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Build and validate payload without sending"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed payload information")

    args = parser.parse_args()

    # Get configuration from environment
    webhook_url = os.getenv("GOVERNANCE_WEBHOOK_URL", "").strip()
    webhook_secret = os.getenv("GOVERNANCE_WEBHOOK_SECRET", "").strip()
    semver_status = os.getenv("SEMVER_STATUS", "unknown").strip()

    if not webhook_url and not args.dry_run:
        print("❌ GOVERNANCE_WEBHOOK_URL environment variable is required")
        return 1

    # Load input files
    try:
        metrics = load_metrics(args.metrics)
        operations = load_operations(args.operations)
    except Exception as e:
        print(f"❌ Failed to load input files: {e}")
        return 1

    # Build payload
    payload = build_payload(metrics, operations, semver_status)

    # Validate payload
    if not validate_payload(payload):
        return 1

    if args.verbose or args.dry_run:
        print("📄 Webhook Payload:")
        print(json.dumps(payload, indent=2))
        print()

    if args.dry_run:
        print("✅ Dry run complete - payload is valid")
        return 0

    # Send webhook
    print(f"📤 Sending webhook to: {webhook_url}")
    success = send_webhook(webhook_url, payload, webhook_secret)

    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
