"""Jira Cloud integration for issue/ticket sync."""

from __future__ import annotations

import base64

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class JiraClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = (settings.jira_base_url or "").rstrip("/")
        self.email = settings.jira_user_email
        self.api_token = settings.jira_api_token
        self.project_key = settings.jira_project_key or "SUP"

    def _configured(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)

    def _headers(self) -> dict[str, str]:
        token = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_issue(self, summary: str, description: str, issue_type: str = "Task") -> dict:
        if not self._configured():
            return {"id": "jira-mock-001", "key": f"{self.project_key}-1", "summary": summary, "status": "To Do"}

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                },
                "issuetype": {"name": issue_type},
            }
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{self.base_url}/rest/api/3/issue", json=payload, headers=self._headers())
            if resp.status_code not in (200, 201):
                logger.error("jira_create_failed", status=resp.status_code, body=resp.text[:200])
                return {"id": "error", "summary": summary, "status": "failed"}
            data = resp.json()
            return {"id": data.get("id", ""), "key": data.get("key", ""), "summary": summary, "status": "open"}

    async def update_issue(self, issue_key: str, fields: dict) -> dict:
        if not self._configured():
            return {"key": issue_key, **fields}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                json={"fields": fields},
                headers=self._headers(),
            )
            if resp.status_code not in (200, 204):
                logger.error("jira_update_failed", status=resp.status_code)
            return {"key": issue_key, **fields}
