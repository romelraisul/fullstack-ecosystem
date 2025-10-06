from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

from .action_refs import extract_action_refs, find_unpinned_external


class EventProcessor:
    def __init__(self, github_client):
        self.github_client = github_client

    async def handle_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        repo = payload.get("repository", {})
        owner = repo.get("owner", {}).get("login")
        name = repo.get("name")
        installation = payload.get("installation", {})
        inst_id = installation.get("id")
        ref = payload.get("ref", "refs/heads/main")
        branch = ref.split("/", 2)[-1]
        commits = payload.get("commits", [])
        changed: list[str] = []
        for c in commits:
            for k in ("added", "modified"):
                for p in c.get(k, []):
                    if p.startswith(".github/workflows/") and p.endswith(".yml"):
                        changed.append(p)
        workflow_paths = sorted(set(changed))
        findings = []
        token = None
        if inst_id is not None:
            try:
                token = await self.github_client.get_installation_token(inst_id)
            except Exception as e:  # noqa: BLE001
                return {"status": "error", "error": f"installation token failure: {e}"}
        head_sha = payload.get("after")
        for path in workflow_paths:
            content = None
            if token and owner and name:
                content = await self.github_client.get_workflow_file(
                    owner, name, path, token, ref=f"heads/{branch}"
                )
            if not content:
                local_path = Path(path)
                if local_path.exists():
                    try:
                        content = local_path.read_text(encoding="utf-8")
                    except Exception:  # noqa: BLE001
                        content = None
            if not content:
                continue
            refs = extract_action_refs(content)
            unpinned = find_unpinned_external(refs)
            if unpinned:
                findings.append({"workflow": path, "issues": [r.to_dict() for r in unpinned]})
        if token and owner and name and head_sha and findings:
            lines = []
            for f in findings:
                lines.append(f"Workflow: {f['workflow']}")
                for issue in f["issues"]:
                    lines.append(
                        f" - {issue['action']}@{issue['ref']} (pinned={issue['pinned']}, internal={issue['internal']})"
                    )
            summary = "Unpinned external action references detected:\n" + "\n".join(lines)
            with contextlib.suppress(Exception):
                await self.github_client.create_check_run(
                    owner,
                    name,
                    "Governance Action Refs",
                    head_sha,
                    token,
                    summary,
                    conclusion="neutral",
                )
        return {
            "status": "ok",
            "branch": branch,
            "workflows_scanned": len(workflow_paths),
            "findings": findings,
        }

    async def handle_pull_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action")
        return {"status": "ignored", "action": action}
