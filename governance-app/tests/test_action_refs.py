from __future__ import annotations
from governance-app.processors.action_refs import extract_action_refs, find_unpinned_external  # type: ignore  # noqa

SAMPLE = """
name: X
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@0.13.0
      - uses: my-org/some-action@main
"""

def test_extract_and_unpinned():
    refs = extract_action_refs(SAMPLE)
    assert any(r.full == 'actions/checkout' for r in refs)
    unpinned = find_unpinned_external(refs)
    # my-org/some-action@main should be flagged
    assert any(r.full == 'my-org/some-action' for r in unpinned)
