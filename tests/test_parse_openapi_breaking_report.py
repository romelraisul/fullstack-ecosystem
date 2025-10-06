import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/parse_openapi_breaking_report.py")


def run(cmd):
    result = subprocess.run([sys.executable, *cmd], capture_output=True, text=True)
    assert (
        result.returncode == 0
    ), f"Command failed: {' '.join(cmd)}\nSTDOUT:{result.stdout}\nSTDERR:{result.stderr}"
    return result


def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_empty_input(tmp_path: Path):
    out = tmp_path / "out.json"
    # No input file -> script creates empty structure
    run([str(SCRIPT), "--input", str(tmp_path / "missing.txt"), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["issues"] == []
    assert data["summary"]["total_lines"] == 0


def test_basic_parsing(tmp_path: Path):
    inp = tmp_path / "breaking.txt"
    lines = [
        "Deleted path /pets",
        "Required field name added",
        "Response changed for 200",
        "Incompatible type change",
    ]
    write_file(inp, "\n".join(lines))
    out = tmp_path / "out.json"
    badge = tmp_path / "badge.json"
    status = tmp_path / "status.json"
    run(
        [
            str(SCRIPT),
            "--input",
            str(inp),
            "--output",
            str(out),
            "--badge-json",
            str(badge),
            "--status-json",
            str(status),
        ]
    )
    data = json.loads(out.read_text())
    assert len(data["issues"]) == 4
    # Ensure classification bucket counts present
    assert data["counters"].get("deleted", 0) == 1
    assert data["counters"].get("required_change", 0) == 1
    assert data["counters"].get("response_changed", 0) == 1
    assert data["counters"].get("incompatible", 0) == 1
    # Badge & status
    badge_data = json.loads(badge.read_text())
    assert "schemaVersion" in badge_data
    status_data = json.loads(status.read_text())
    assert status_data["breaking"] is True


def test_custom_config(tmp_path: Path):
    inp = tmp_path / "custom.txt"
    write_file(inp, "CRITICAL change in model")
    out = tmp_path / "out.json"
    cfg = tmp_path / "patterns.json"
    cfg.write_text('[{"label":"critical","pattern":"CRITICAL"}]', encoding="utf-8")
    run([str(SCRIPT), "--input", str(inp), "--output", str(out), "--config", str(cfg)])
    data = json.loads(out.read_text())
    assert data["counters"].get("critical", 0) == 1
