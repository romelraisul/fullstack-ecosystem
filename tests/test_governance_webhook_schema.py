import json
import pathlib

from jsonschema import Draft202012Validator

SCHEMA_PATH = pathlib.Path("docs/governance_webhook.schema.json")

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    SCHEMA = json.load(f)

# Select a validator class resilient to draft 2020 (fallback: Draft202012Validator)
Validator = Draft202012Validator


def make_payload(reasons):
    return {
        "event": "governance_notice",
        "version": 1,
        "sha": "abcdef1",
        "semver_status": "ok",
        "stability_ratio": 0.95,
        "reasons": reasons,
        "operations": {"added": 1, "removed": 0},
    }


def test_valid_failure_reason():
    payload = make_payload(["semver_fail"])
    Validator(SCHEMA).validate(payload)


def test_valid_recovery_reason():
    payload = make_payload(["stability_recovered", "placeholder_recovered"])
    Validator(SCHEMA).validate(payload)


def test_invalid_reason_rejected():
    payload = make_payload(["not_a_reason"])
    try:
        Validator(SCHEMA).validate(payload)
    except Exception:
        return
    raise AssertionError("Invalid reason should have failed validation")


def test_operations_counts_non_negative():
    p = make_payload(["semver_fail"])
    p["operations"]["added"] = -1
    try:
        Validator(SCHEMA).validate(p)
    except Exception:
        return
    raise AssertionError("Negative added count should fail")
