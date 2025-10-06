import contextlib
import json
import time
from collections.abc import Iterator
from pathlib import Path

import app.bridge as bridge  # type: ignore


@contextlib.contextmanager
def temp_bridge_data(tmp_path: Path) -> Iterator[Path]:
    """Monkeypatch bridge.DATA_PATH to a temporary file, initializing empty structure.

    Yields the temp path used so tests can inspect or modify underlying data.
    """
    original = bridge.DATA_PATH
    data_file = tmp_path / "bridge_data.json"
    try:
        bridge.DATA_PATH = data_file  # type: ignore
        # initialize empty structure
        data_file.parent.mkdir(parents=True, exist_ok=True)
        data_file.write_text(json.dumps({"inputs": [], "experiments": []}), encoding="utf-8")
        yield data_file
    finally:
        bridge.DATA_PATH = original  # type: ignore


def read_bridge_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add_raw_input(path: Path, **overrides):
    data = read_bridge_json(path)
    next_id = (data["inputs"][-1]["id"] + 1) if data["inputs"] else 1
    item = {
        "id": next_id,
        "title": overrides.get("title", f"Title {next_id}"),
        "problem": overrides.get("problem", "A test problem"),
        "hypothesis": overrides.get("hypothesis"),
        "impact_score": overrides.get("impact_score", 5),
        "tags": overrides.get("tags", ["tag"]),
        "owner": overrides.get("owner"),
        "status": overrides.get("status", "new"),
        "created_at": time.time(),
    }
    data["inputs"].append(item)
    path.write_text(json.dumps(data), encoding="utf-8")
    return item
