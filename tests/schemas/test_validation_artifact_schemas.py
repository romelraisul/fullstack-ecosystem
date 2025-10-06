import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
WRAPPER = SCRIPTS / "run_observability_validations.py"
SCHEMAS = ROOT / "schemas"


def load_schema(name: str):
    return json.loads((SCHEMAS / name).read_text())


def validate(instance, schema):
    """Very small subset of JSON Schema validation (presence + type + enum). Avoid external dep."""

    def fail(msg):
        raise AssertionError(msg)

    if schema.get("type") == "object":
        if not isinstance(instance, dict):
            fail(f"Expected object, got {type(instance)}")
        required = schema.get("required", [])
        for k in required:
            if k not in instance:
                fail(f"Missing required key {k}")
        props = schema.get("properties", {})
        for k, v in instance.items():
            subschema = props.get(k)
            if subschema:
                validate(v, subschema)
        enum = schema.get("enum")
        if enum and instance not in enum:
            fail(f"Value {instance} not in enum {enum}")
    elif schema.get("type") == "array":
        if not isinstance(instance, list):
            fail(f"Expected array got {type(instance)}")
        items_schema = schema.get("items")
        if items_schema:
            for it in instance:
                validate(it, items_schema)
    elif schema.get("type") == "integer":
        if not isinstance(instance, int):
            fail(f"Expected integer got {type(instance)}")
        if "enum" in schema and instance not in schema["enum"]:
            fail(f"Integer {instance} not in enum {schema['enum']}")
    elif schema.get("type") == "string":
        if not isinstance(instance, str):
            fail(f"Expected string got {type(instance)}")
        if "enum" in schema and instance not in schema["enum"]:
            fail(f"String {instance} not in enum {schema['enum']}")
    elif schema.get("type") == "number":
        if not isinstance(instance, (int, float)):
            fail(f"Expected number got {type(instance)}")
    elif isinstance(schema.get("type"), list):
        if not any(
            (t == "null" and instance is None)
            or (t == "string" and isinstance(instance, str))
            or (t == "integer" and isinstance(instance, int))
            for t in schema["type"]
        ):
            fail(f"Type {type(instance)} not in allowed {schema['type']}")
    # Allow pass-through for others
    return True


def test_artifact_schemas(tmp_path):
    # Create minimal baseline/current and rules/taxonomy as in wrapper test
    baseline = [
        {"title": f"Panel {i}", "gridPos": {"x": i * 2, "y": 0, "w": 2, "h": 2}} for i in range(5)
    ]
    current = list(baseline)
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline))
    current_path.write_text(json.dumps(current))

    rules_yaml = """
    groups:
      - name: test
        rules:
          - alert: SampleAlert
            expr: up == 1
            labels:
              severity: critical
    """.strip()
    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(rules_yaml)

    taxonomy = {"alerts": [{"alert": "SampleAlert", "severity": "critical", "runbook": "r"}]}
    taxonomy_path = tmp_path / "taxonomy.json"
    taxonomy_path.write_text(json.dumps(taxonomy))

    layout_report = tmp_path / "layout_report.json"
    alerts_report = tmp_path / "alerts_report.json"
    index_json = tmp_path / "index.json"
    combined_metrics = tmp_path / "combined.prom"

    cmd = [
        sys.executable,
        str(WRAPPER),
        "--layout-baseline",
        str(baseline_path),
        "--layout-current-glob",
        str(current_path),
        "--alerts-rules",
        str(rules_path),
        "--alerts-taxonomy",
        str(taxonomy_path),
        "--layout-report",
        str(layout_report),
        "--alerts-report",
        str(alerts_report),
        "--out-index",
        str(index_json),
        "--out-metrics",
        str(combined_metrics),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Wrapper failed: {res.stderr}\n{res.stdout}"

    layout_doc = json.loads(layout_report.read_text())
    alerts_doc = json.loads(alerts_report.read_text())
    index_doc = json.loads(index_json.read_text())

    validate(layout_doc, load_schema("layout_report.schema.json"))
    validate(alerts_doc, load_schema("alerts_report.schema.json"))
    validate(index_doc, load_schema("validations_index.schema.json"))

    # Spot check some semantics beyond schema
    assert layout_doc["current_panel_count"] == 5
    assert alerts_doc["error_count"] == 0
    assert index_doc["overall_status"] == "pass"
