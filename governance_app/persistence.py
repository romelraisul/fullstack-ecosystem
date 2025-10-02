from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path("governance-app-data.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  repo TEXT NOT NULL,
  branch TEXT NOT NULL,
  workflows_scanned INTEGER NOT NULL,
  findings_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  workflow TEXT NOT NULL,
  action TEXT NOT NULL,
  ref TEXT NOT NULL,
  pinned INTEGER NOT NULL,
  internal INTEGER NOT NULL,
  raw JSON NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);
"""

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def record_run(repo: str, branch: str, workflows_scanned: int, findings: list[dict[str, Any]]) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs(repo, branch, workflows_scanned, findings_count) VALUES (?,?,?,?)",
            (repo, branch, workflows_scanned, len(findings)),
        )
        run_id = cur.lastrowid
        for f in findings:
            for issue in f.get("issues", []):
                cur.execute(
                    "INSERT INTO findings(run_id, workflow, action, ref, pinned, internal, raw) VALUES (?,?,?,?,?,?,?)",
                    (
                        run_id,
                        f.get("workflow"),
                        issue.get("action"),
                        issue.get("ref"),
                        1 if issue.get("pinned") else 0,
                        1 if issue.get("internal") else 0,
                        json.dumps(issue),
                    ),
                )
        conn.commit()
        return run_id


def recent_runs(limit: int = 20, offset: int = 0, repo: str | None = None, branch: str | None = None) -> Iterable[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if repo:
        clauses.append("repo = ?")
        params.append(repo)
    if branch:
        clauses.append("branch = ?")
        params.append(branch)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    query = (
        "SELECT id, ts, repo, branch, workflows_scanned, findings_count FROM runs"
        + where
        + " ORDER BY id DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        for row in rows:
            yield {"id": row[0], "ts": row[1], "repo": row[2], "branch": row[3], "workflows_scanned": row[4], "findings_count": row[5]}


def list_findings(
    run_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    repo: str | None = None,
    branch: str | None = None,
    workflow: str | None = None,
    action: str | None = None,
):
    # Join runs for repo/branch filtering
    query = (
        "SELECT f.id, f.run_id, f.workflow, f.action, f.ref, f.pinned, f.internal, f.raw "
        "FROM findings f JOIN runs r ON f.run_id = r.id"
    )
    clauses = []
    params: list[Any] = []
    if run_id is not None:
        clauses.append("f.run_id = ?")
        params.append(run_id)
    if repo:
        clauses.append("r.repo = ?")
        params.append(repo)
    if branch:
        clauses.append("r.branch = ?")
        params.append(branch)
    if workflow:
        clauses.append("f.workflow = ?")
        params.append(workflow)
    if action:
        clauses.append("f.action = ?")
        params.append(action)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    query += where + " ORDER BY f.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        for row in cur.fetchall():
            yield {
                "id": row[0],
                "run_id": row[1],
                "workflow": row[2],
                "action": row[3],
                "ref": row[4],
                "pinned": bool(row[5]),
                "internal": bool(row[6]),
                "raw": json.loads(row[7]) if row[7] else None,
            }
