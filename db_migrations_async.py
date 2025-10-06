"""Async migration scaffold.

This module provides a minimal async migration runner that can be extended.
If POSTGRES_DSN is unset or asyncpg isn't available, it becomes a no-op.
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import pathlib
from collections.abc import Awaitable, Callable, Sequence

logger = logging.getLogger(__name__)

MigrationFunc = Callable[["Connection"], Awaitable[None]]  # type: ignore


class Migration:
    def __init__(self, name: str, func: MigrationFunc):
        self.name = name
        self.func = func


async def run_async_migrations(dsn: str | None, migrations: Sequence[Migration]):
    if not dsn:
        logger.info("No POSTGRES_DSN provided; skipping async migrations")
        return
    try:
        import asyncpg  # type: ignore
    except Exception:
        logger.warning("asyncpg not installed; cannot run migrations")
        return
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations(
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMPTZ DEFAULT now()
        )"""
        )
        applied_rows = await conn.fetch("SELECT name FROM schema_migrations")
        applied = {r[0] for r in applied_rows}
        for m in migrations:
            if m.name in applied:
                continue
            logger.info("Applying migration %s", m.name)
            await m.func(conn)  # type: ignore
            await conn.execute("INSERT INTO schema_migrations(name) VALUES($1)", m.name)
        logger.info("Async migrations complete")
    finally:
        await conn.close()


def discover_migrations(path: str = "migrations") -> list[Migration]:
    """Dynamically discover migration modules in a directory.

    Each file named ``XXXX_description.py`` exporting a coroutine function ``upgrade(conn)``
    will be loaded as a migration with name derived from the stem (e.g. 0002_add_table).
    """
    root = pathlib.Path(path)
    found: list[Migration] = []
    if not root.exists():
        return found
    for file in sorted(root.glob("[0-9][0-9][0-9][0-9]_*.py")):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        if not spec or not spec.loader:  # pragma: no cover
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore
        except Exception as e:  # pragma: no cover
            logger.warning("Failed loading migration %s: %s", file.name, e)
            continue
        upgrade = getattr(module, "upgrade", None)
        if upgrade and inspect.iscoroutinefunction(upgrade):
            found.append(Migration(file.stem, upgrade))
    return found


# Example placeholder migration
async def example_initial(conn):  # pragma: no cover
    await conn.execute("CREATE TABLE IF NOT EXISTS example(id SERIAL PRIMARY KEY, note TEXT)")


DEFAULT_MIGRATIONS = [Migration("0001_example_initial", example_initial)] + discover_migrations()

__all__ = ["Migration", "run_async_migrations", "DEFAULT_MIGRATIONS", "discover_migrations"]
