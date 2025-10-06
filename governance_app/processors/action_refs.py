from __future__ import annotations

import re
from collections.abc import Iterable

USE_PATTERN = re.compile(r"^[ \t-]*uses:\s*([\w./-]+)@([^\s#]+)")

EXCLUDE_INTERNAL_PREFIXES = {"actions/checkout", "actions/cache"}


class ActionRef:
    def __init__(self, full: str, ref: str):
        self.full = full
        self.ref = ref

    def is_pinned(self) -> bool:
        return bool(re.fullmatch(r"[0-9a-fA-F]{40}", self.ref))

    def is_internal(self) -> bool:
        return any(self.full.startswith(p) for p in EXCLUDE_INTERNAL_PREFIXES)

    def to_dict(self):
        return {
            "action": self.full,
            "ref": self.ref,
            "pinned": self.is_pinned(),
            "internal": self.is_internal(),
        }


def extract_action_refs(workflow_content: str) -> list[ActionRef]:
    refs: list[ActionRef] = []
    for line in workflow_content.splitlines():
        m = USE_PATTERN.search(line)
        if m:
            refs.append(ActionRef(m.group(1), m.group(2)))
    return refs


def find_unpinned_external(refs: Iterable[ActionRef]) -> list[ActionRef]:
    return [r for r in refs if not r.is_internal() and not r.is_pinned()]
