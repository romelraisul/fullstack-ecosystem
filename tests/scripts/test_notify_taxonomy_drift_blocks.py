import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, ROOT.as_posix())

TAXONOMY = {
    "alerts": [
        {"alert": "Old", "severity": "low", "deprecated": False, "runbook": "ok"},
        {"alert": "New", "severity": "medium", "deprecated": False, "runbook": "ok"},
    ]
}


def test_blocks_payload(tmp_path, monkeypatch):
    taxonomy = tmp_path / "alerts_taxonomy.json"
    taxonomy.write_text(json.dumps(TAXONOMY))
    dummy_rules = tmp_path / "rules.yml"
    # Provide a rules file containing only one alert so the taxonomy has drift (unused alert present)
    dummy_rules.write_text("groups:\n - name: g1\n   rules:\n   - alert: Old\n")

    captured = {}
    import urllib.request as _ur

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"ok"

    def fake_urlopen(req, timeout=10):
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return FakeResp()

    monkeypatch.setattr(_ur, "urlopen", fake_urlopen)

    import scripts.notify_taxonomy_drift as mod

    # Avoid YAML parsing of rules; just return expected set
    # Only Old is active according to rules, New will appear as drift
    monkeypatch.setattr(mod, "load_rules", lambda p: {"Old"})

    os.environ["TAXONOMY_SLACK_BLOCKS"] = "1"
    sys.argv = [
        "x",
        "--rules",
        dummy_rules.as_posix(),
        "--taxonomy",
        taxonomy.as_posix(),
        "--webhook",
        "https://example/hook",
    ]
    mod.main()
    payload = captured.get("payload")
    assert payload and "blocks" in payload
    blob = json.dumps(payload["blocks"]).lower()
    # Expect drift section referencing 'new' and presence of 'old' in counts list
    assert "new" in blob
