"""Tests for SaaS plan enforcement."""

import pytest
from fastapi import HTTPException

from src.saas import plan_gates


class _FakeDB:
    plan_id = "free"

    @classmethod
    def get_tenant_subscription(cls, tenant_id: str) -> dict:
        return {"plan_id": cls.plan_id, "tenant_id": tenant_id}


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    _FakeDB.plan_id = "free"
    monkeypatch.setattr(plan_gates, "db", _FakeDB)


def test_free_plan_blocks_voice():
    with pytest.raises(HTTPException) as exc:
        plan_gates.require_channel("tenant-abc", "voice")
    assert exc.value.status_code == 402
    assert exc.value.detail["code"] == "plan_upgrade_required"


def test_free_plan_allows_chat():
    plan_gates.require_channel("tenant-abc", "chat")


def test_free_plan_blocks_voice_agent():
    with pytest.raises(HTTPException):
        plan_gates.require_agent("tenant-abc", "voice_support")


def test_integration_limit():
    existing = {
        "hubspot_api_key": "x",
        "zendesk_api_key": "y",
        "zendesk_subdomain": "z",
        "slack_webhook_url": "https://hooks.slack.com/x",
        "intercom_access_token": "tok",
        "jira_api_token": "j",
        "jira_base_url": "https://jira.example.com",
    }
    with pytest.raises(HTTPException):
        plan_gates.require_integration_capacity(
            "tenant-abc",
            {"freshdesk_api_key": "fd"},
            existing,
        )


def test_tenant_collection_name():
    from src.rag.vector_store import tenant_collection_name

    assert tenant_collection_name("default") == "knowledge_base"
    assert tenant_collection_name("tenant-abc123").startswith("kb_")
