import json
import pathlib
import subprocess
import sys

SCRIPT = pathlib.Path("scripts/classify_operation_changes.py")


def run(args):
    cmd = [sys.executable, str(SCRIPT)] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_no_previous_all_added(tmp_path):
    new_spec = {"openapi": "3.0.0", "paths": {"/pets": {"get": {}}, "/users": {"post": {}}}}
    new_file = tmp_path / "new.json"
    out_file = tmp_path / "out.json"
    write_json(new_file, new_spec)
    r = run(["--new", str(new_file), "--out", str(out_file)])
    assert r.returncode == 0
    data = load_json(out_file)
    added = {(o["method"], o["path"]) for o in data["operations_added"]}
    removed = data["operations_removed"]
    assert len(removed) == 0
    assert added == {("GET", "/pets"), ("POST", "/users")}
    assert data["counts"]["added"] == 2
    assert data["counts"]["removed"] == 0


def test_only_removals(tmp_path):
    old_spec = {
        "openapi": "3.0.0",
        "paths": {"/obsolete": {"delete": {}}, "/stay": {"get": {}}, "/gone": {"patch": {}}},
    }
    new_spec = {"openapi": "3.0.0", "paths": {"/stay": {"get": {}}}}
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    out_file = tmp_path / "out.json"
    write_json(old_file, old_spec)
    write_json(new_file, new_spec)
    r = run(["--old", str(old_file), "--new", str(new_file), "--out", str(out_file)])
    assert r.returncode == 0
    data = load_json(out_file)
    removed = {(o["method"], o["path"]) for o in data["operations_removed"]}
    assert removed == {("DELETE", "/obsolete"), ("PATCH", "/gone")}
    assert data["counts"]["removed"] == 2
    assert data["counts"]["added"] == 0


def test_mixed_changes(tmp_path):
    old_spec = {
        "openapi": "3.0.0",
        "paths": {"/keep": {"get": {}}, "/drop": {"post": {}}, "/swap": {"get": {}}},
    }
    new_spec = {
        "openapi": "3.0.0",
        "paths": {"/keep": {"get": {}}, "/add": {"put": {}}, "/swap": {"post": {}}},
    }
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    out_file = tmp_path / "out.json"
    write_json(old_file, old_spec)
    write_json(new_file, new_spec)
    r = run(["--old", str(old_file), "--new", str(new_file), "--out", str(out_file)])
    assert r.returncode == 0
    data = load_json(out_file)
    added = {(o["method"], o["path"]) for o in data["operations_added"]}
    removed = {(o["method"], o["path"]) for o in data["operations_removed"]}
    assert added == {("PUT", "/add"), ("POST", "/swap")}
    assert removed == {("POST", "/drop"), ("GET", "/swap")}
    assert data["counts"]["added"] == 2
    assert data["counts"]["removed"] == 2
