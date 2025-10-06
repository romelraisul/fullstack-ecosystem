import json
from pathlib import Path

import pytest

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    pytest.skip("jsonschema library not installed", allow_module_level=True)

SCHEMA_PATH = Path("schemas/stability-metrics.schema.json")
METRICS_SAMPLE_PATH = Path("status/stability-metrics.json")


@pytest.fixture(scope="session")
def schema():
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text())


@pytest.mark.parametrize(
    "sample",
    [
        # Full rich metrics sample (normal mode)
        {
            "schema_version": 1,
            "timestamp": 1727500000,
            "breaking": False,
            "incompatible": 0,
            "deleted_or_removed": 0,
            "score": 100,
            "window_size": 30,
            "window_total_count": 10,
            "window_stable_count": 10,
            "window_stability_ratio": 1.0,
            "current_stable_streak": 10,
            "longest_stable_streak": 25,
            "window_mean_score": 98.7,
            "badge": {"label": "stability", "message": "stable", "color": "brightgreen"},
        },
        # Minimal placeholder object allowed when metrics generation is skipped
        {"schema_version": 1, "window_stability_ratio": 1.0, "placeholder": True},
    ],
)
def test_schema_accepts_valid_sample(sample, schema):
    jsonschema.validate(instance=sample, schema=schema)


def test_generated_metrics_matches_schema(schema):
    # Only validate if metrics file exists (main branch run); otherwise skip gracefully
    if not METRICS_SAMPLE_PATH.exists():
        pytest.skip("stability-metrics.json not present in workspace")
    metrics = json.loads(METRICS_SAMPLE_PATH.read_text())
    jsonschema.validate(instance=metrics, schema=schema)
