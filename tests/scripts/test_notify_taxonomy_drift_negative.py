import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, ROOT.as_posix())

# Taxonomy marks an alert deprecated and missing runbook; rules include it so errors + drift appear
TAX = {"alerts": [{"alert": "LegacyAlert", "severity": "high", "deprecated": True, "runbook": ""}]}


def test_negative_blocks(tmp_path, monkeypatch):
    taxonomy = tmp_path / "alerts_taxonomy.json"
    taxonomy.write_text(json.dumps(TAX))
    rules = tmp_path / "rules.yml"
    # Active rule referencing deprecated alert missing runbook
    rules.write_text("groups:\n - name: g\n   rules:\n   - alert: LegacyAlert\n")

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

    os.environ["TAXONOMY_SLACK_BLOCKS"] = "1"
    sys.argv = [
        "x",
        "--rules",
        rules.as_posix(),
        "--taxonomy",
        taxonomy.as_posix(),
        "--webhook",
        "https://example/hook",
    ]
    mod.main()

    payload = captured.get("payload")
    assert payload and "blocks" in payload
    text_blob = json.dumps(payload["blocks"]).lower()
    # Expect deprecated + runbook missing surfaces as both Errors or Drift lines
    assert "deprecated alert" in text_blob or "deprecated alert(s)" in text_blob
    assert "missing runbook" in text_blob
