from __future__ import annotations

import time
from typing import Any

import httpx
import jwt  # type: ignore

from .config import get_settings

# NOTE: PyJWT is required but not listed explicitly; cryptography handles signing.
# If PyJWT isn't available, add it to requirements.


class GitHubAuthError(Exception):
    pass


class GitHubClient:
    def __init__(self):
        self.settings = get_settings()
        self._cached_app_token: str | None = None
        self._cached_app_token_exp: float = 0.0

    def _generate_jwt(self) -> str:
        if not self.settings.app_id or not self.settings.private_key:
            raise GitHubAuthError("App ID or Private Key missing")
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (8 * 60),  # 8 minutes
            "iss": self.settings.app_id,
        }
        token = jwt.encode(payload, self.settings.private_key, algorithm="RS256")
        return token if isinstance(token, str) else token.decode()

    async def get_installation_token(self, installation_id: int) -> str:
        jwt_token = self._generate_jwt()
        url = f"{self.settings.github_api_url}/app/installations/{installation_id}/access_tokens"
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            }
        ) as client:
            resp = await client.post(url)
            if resp.status_code >= 300:
                raise GitHubAuthError(
                    f"Failed to get installation token: {resp.status_code} {resp.text}"
                )
            data: dict[str, Any] = resp.json()
            return data["token"]

    async def get_workflow_file(
        self, owner: str, repo: str, path: str, token: str, ref: str = "heads/main"
    ) -> str | None:
        # GitHub raw content API
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
        async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.text
            return None

    async def create_check_run(
        self,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        token: str,
        summary: str,
        conclusion: str | None = None,
    ):
        url = f"{self.settings.github_api_url}/repos/{owner}/{repo}/check-runs"
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": "completed" if conclusion else "in_progress",
        }
        if conclusion:
            payload["conclusion"] = conclusion
        output = {
            "title": name,
            "summary": summary[:65000],
        }
        payload["output"] = output
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        ) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 300:
                raise GitHubAuthError(f"Check run creation failed: {resp.status_code} {resp.text}")
            return resp.json()
