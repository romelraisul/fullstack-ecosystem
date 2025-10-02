from __future__ import annotations
from typing import Any, Dict
from .action_refs import extract_action_refs, find_unpinned_external

class EventProcessor:
    def __init__(self, github_client):
        self.github_client = github_client

    async def handle_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = payload.get("repository", {})
        owner = repo.get("owner", {}).get("login")
        name = repo.get("name")
        ref = payload.get("ref", "refs/heads/main")
        branch = ref.split("/", 2)[-1]
        # For simplicity just look at a fixed set of workflow paths in this example
        workflow_paths = [
            ".github/workflows/workflow-lint.yml",
        ]
        findings = []
        for path in workflow_paths:
            # In full implementation, list changed workflow files from payload
            content = None  # Placeholder; would fetch with installation token
            if content:
                refs = extract_action_refs(content)
                unpinned = find_unpinned_external(refs)
                if unpinned:
                    findings.append({"workflow": path, "issues": [r.to_dict() for r in unpinned]})
        return {"status": "ok", "branch": branch, "findings": findings}

    async def handle_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action")
        return {"status": "ignored", "action": action}
