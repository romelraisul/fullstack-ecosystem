from __future__ import annotations

import time
from typing import Any

import httpx
import jwt  # type: ignore

from ..utils.resilience import (
    RetryStrategy,
    async_retry_with_backoff,
    with_metrics,
)
from .config import get_settings


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
        payload = {"iat": now - 60, "exp": now + (8 * 60), "iss": self.settings.app_id}
        token = jwt.encode(payload, self.settings.private_key, algorithm="RS256")
        return token if isinstance(token, str) else token.decode()

    @with_metrics("github_installation_token")
    async def get_installation_token(self, installation_id: int) -> str:
        jwt_token = self._generate_jwt()
        url = f"{self.settings.github_api_url}/app/installations/{installation_id}/access_tokens"

        async def _make_request():
            async with httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=30.0,
            ) as client:
                resp = await client.post(url)
                if resp.status_code >= 300:
                    raise GitHubAuthError(
                        f"Failed to get installation token: {resp.status_code} {resp.text}"
                    )
                data: dict[str, Any] = resp.json()
                return data["token"]

        result = await async_retry_with_backoff(
            _make_request,
            max_attempts=3,
            base_delay=1.0,
            strategy=RetryStrategy.JITTERED_EXPONENTIAL,
            exceptions=(httpx.RequestError, httpx.TimeoutException, GitHubAuthError),
        )

        if not result.success:
            raise result.last_exception

        return await _make_request()

    @with_metrics("github_workflow_file")
    async def get_workflow_file(
        self, owner: str, repo: str, path: str, token: str, ref: str = "heads/main"
    ) -> str | None:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"

        async def _fetch_file():
            async with httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"}, timeout=30.0
            ) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    return r.text
                elif r.status_code == 404:
                    return None
                else:
                    raise httpx.HTTPStatusError(
                        f"HTTP {r.status_code}", request=r.request, response=r
                    )

        try:
            result = await async_retry_with_backoff(
                _fetch_file,
                max_attempts=3,
                base_delay=0.5,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                exceptions=(httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError),
            )

            if result.success:
                return await _fetch_file()
            else:
                return None
        except Exception:
            return None

    @with_metrics("github_check_run")
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
        output = {"title": name, "summary": summary[:65000]}
        payload["output"] = output

        async def _create_check():
            async with httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=30.0,
            ) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 300:
                    raise httpx.HTTPStatusError(
                        f"Failed to create check run: {resp.status_code} {resp.text}",
                        request=resp.request,
                        response=resp,
                    )
                return resp.json()

        result = await async_retry_with_backoff(
            _create_check,
            max_attempts=3,
            base_delay=1.0,
            strategy=RetryStrategy.JITTERED_EXPONENTIAL,
            exceptions=(httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError),
        )

        if not result.success:
            raise result.last_exception

        return await _create_check()

    async def _create_check():
        # Implementation for creating the check
        if resp.status_code >= 300:
            raise GitHubAuthError(f"Check run creation failed: {resp.status_code} {resp.text}")
        return resp.json()
