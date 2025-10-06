import json
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "agent_registry.schema.json"
REGISTRY_PATH = ROOT / "autogen" / "agents" / "agent_registry.json"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "agent_registry.schema.json missing"


def test_registry_file_exists():
    assert REGISTRY_PATH.exists(), "agent_registry.json missing (expected for validation)"


def test_registry_validates_against_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data_raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data_raw, list), "Registry root must be a list of agent objects"
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data_raw))
    msg = "\n".join(sorted({e.message for e in errors}))
    assert not errors, f"Registry schema violations:\n{msg}"


def test_required_threshold_fields_present_if_defined():
    # If one latency threshold is present both warning and critical should be present (consistency heuristic)
    data_raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data_raw:
        if "latency_p95_warning_seconds" in entry or "latency_p95_critical_seconds" in entry:
            assert (
                "latency_p95_warning_seconds" in entry and "latency_p95_critical_seconds" in entry
            ), f"Agent {entry.get('name')} missing paired latency thresholds"
