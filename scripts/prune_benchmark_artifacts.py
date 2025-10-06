"""Prune benchmark artifact JSON files, keeping only the most recent N.

Selection heuristic:
  - Files matching pattern quantile_bench_*.json in artifacts/ (default dir)
  - Sorted by modification time descending; keep first N, delete the rest.

Usage:
  python scripts/prune_benchmark_artifacts.py --dir artifacts --keep 100

Exit codes:
  0 success (even if nothing to prune)
  1 unexpected error
"""

from __future__ import annotations

import argparse
from pathlib import Path


def prune(directory: Path, keep: int) -> int:
    if keep < 0:
        raise ValueError("keep must be >= 0")
    if not directory.exists():
        return 0
    files: list[Path] = sorted(
        [p for p in directory.glob("quantile_bench_*.json") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if len(files) <= keep:
        return 0
    to_delete = files[keep:]
    for p in to_delete:
        try:
            p.unlink()
        except OSError:
            # Best-effort; continue
            pass
    return len(to_delete)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune benchmark artifacts")
    parser.add_argument("--dir", default="artifacts", help="Artifacts directory")
    parser.add_argument("--keep", type=int, default=100, help="Number of newest artifacts to keep")
    args = parser.parse_args()

    deleted = prune(Path(args.dir), args.keep)
    print(f"Deleted {deleted} old benchmark artifact(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
