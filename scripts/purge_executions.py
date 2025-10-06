"""Manual purge utility for workflow executions.

Usage:
  python -m scripts.purge_executions [retention]

If retention argument not supplied, uses WORKFLOW_EXECUTION_RETENTION env var (default 1000).
Deletes oldest executions beyond retention size (leverages repository prune logic which keeps most recent).
"""

from __future__ import annotations

import sys

from autogen.advanced_backend import get_execution_retention, get_workflows_repo


def main(argv: list[str]) -> int:
    if not get_workflows_repo():
        print("Repository not available (DB path missing or initialization failed)")
        return 1
    if len(argv) > 1:
        try:
            retention = int(argv[1])
        except ValueError:
            print("Invalid retention value", argv[1])
            return 2
    else:
        retention = get_execution_retention()
    if retention <= 0:
        print("Retention <= 0 (purge disabled). Nothing to do.")
        return 0
    repo = get_workflows_repo()
    try:
        deleted = repo.prune_executions(retention)  # type: ignore[arg-type]
    except Exception as e:  # pragma: no cover
        print("Purge failed:", e)
        return 3
    print(f"Purged {deleted} old workflow executions (retention={retention})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv))
