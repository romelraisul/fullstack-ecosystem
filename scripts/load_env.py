"""Lightweight .env loader (no external deps).

Usage:
  from scripts.load_env import load_env
  load_env()  # loads .env if present, does not override already-set vars

Design: minimal; only supports KEY=VALUE lines, ignores comments and blanks.
"""

from __future__ import annotations

from pathlib import Path


def load_env(path: str | None = None) -> None:
    candidate = Path(path or ".env")
    if not candidate.exists():
        return
    for raw in candidate.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k and k not in __import__("os").environ:
            __import__("os").environ[k] = v


__all__ = ["load_env"]
