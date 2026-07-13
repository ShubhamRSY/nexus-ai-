"""Plan-based feature gates for Nexus Cloud tiers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from src.auth import AuthContext
from src.config import get_settings, load_agent_config
from src.database import db
from src.saas.provisioning import get_plan

_CHANNEL_ALIASES = {
    "voice": "voice",
    "telephony": "voice",
    "whatsapp": "whatsapp",
    "sms": "sms",
    "messenger": "messenger",
    "instagram": "instagram",
    "chat": "chat",
    "email": "email",
    "copilot": "copilot",
}

_FALLBACK_PLAN: dict[str, Any] = {"name": "Free", "channels": ["chat", "email"], "agents": 2, "integrations": 5}

# Agents allowed per plan (matches marketing limits).
_PLAN_AGENTS: dict[str, list[str] | None] = {
    "free": ["chat_support", "copilot"],
    "starter": ["chat_support", "copilot", "voice_support"],
    "growth": ["chat_support", "copilot", "voice_support", "whatsapp_support"],
    "enterprise": None,
}

# Credential keys that indicate an integration is configured (provider → keys).
_PROVIDER_CREDENTIALS: dict[str, tuple[str, ...]] = {
    "hubspot": ("hubspot_api_key",),
    "salesforce": ("salesforce_client_id", "salesforce_client_secret"),
    "zendesk": ("zendesk_api_key", "zendesk_subdomain"),
    "freshdesk": ("freshdesk_api_key", "freshdesk_domain"),
    "intercom": ("intercom_access_token",),
    "twilio": ("twilio_account_sid", "twilio_auth_token"),
    "slack": ("slack_webhook_url",),
    "jira": ("jira_api_token", "jira_base_url"),
    "meta": ("meta_page_access_token",),
    "servicenow": ("servicenow_api_key", "servicenow_instance"),
}


def tenant_plan_id(tenant_id: str) -> str:
    sub = db.get_tenant_subscription(tenant_id)
    return str((sub or {}).get("plan_id") or "free")


def _resolve_plan(tenant_id: str) -> dict[str, Any]:
    return get_plan(tenant_plan_id(tenant_id)) or get_plan("free") or _FALLBACK_PLAN


def plan_allows_channel(tenant_id: str, channel: str) -> bool:
    plan = _resolve_plan(tenant_id)
    allowed = {c.lower() for c in plan.get("channels", [])}
    return _CHANNEL_ALIASES.get(channel.lower(), channel.lower()) in allowed


def require_channel(tenant_id: str, channel: str) -> None:
    if plan_allows_channel(tenant_id, channel):
        return
    plan = _resolve_plan(tenant_id)
    raise HTTPException(
        status_code=402,
        detail={
            "code": "plan_upgrade_required",
            "message": f"{channel.title()} is not included on the {plan['name']} plan. Upgrade to unlock.",
            "upgrade_url": "/contact",
        },
    )


def require_channel_for_context(ctx: AuthContext | None, channel: str) -> None:
    """Apply plan gates only when the caller is an authenticated tenant."""
    if ctx is None:
        return
    require_channel(ctx.tenant_id, channel)


def allowed_agents(tenant_id: str) -> list[str] | None:
    plan_id = tenant_plan_id(tenant_id)
    if plan_id in _PLAN_AGENTS:
        return _PLAN_AGENTS[plan_id]
    plan = _resolve_plan(tenant_id)
    limit = int(plan.get("agents") or 999)
    all_agents = list(load_agent_config().get("agents", {}).keys())
    return all_agents[:limit] if limit < len(all_agents) else None


def require_agent(tenant_id: str, agent_id: str) -> None:
    allowed = allowed_agents(tenant_id)
    if allowed is None:
        return
    if agent_id in allowed:
        return
    plan = _resolve_plan(tenant_id)
    raise HTTPException(
        status_code=402,
        detail={
            "code": "plan_upgrade_required",
            "message": (
                f"Agent '{agent_id}' is not included on the {plan['name']} plan "
                f"({len(allowed)} agents max). Upgrade to unlock."
            ),
            "upgrade_url": "/contact",
        },
    )


def require_agent_for_context(ctx: AuthContext | None, agent_id: str) -> None:
    if ctx is None:
        return
    require_agent(ctx.tenant_id, agent_id)


def count_configured_integrations(credentials: dict[str, str]) -> int:
    """Count distinct integrations with at least one credential set."""
    count = 0
    for _provider, keys in _PROVIDER_CREDENTIALS.items():
        if any(str(credentials.get(k) or "").strip() for k in keys):
            count += 1
    return count


def require_integration_capacity(
    tenant_id: str,
    updates: dict[str, str],
    existing: dict[str, str],
) -> None:
    plan = _resolve_plan(tenant_id)
    limit = int(plan.get("integrations") or 62)
    merged = {**existing, **{k: v for k, v in updates.items() if v}}
    if count_configured_integrations(merged) <= limit:
        return
    raise HTTPException(
        status_code=402,
        detail={
            "code": "plan_upgrade_required",
            "message": (
                f"Your {plan['name']} plan includes up to {limit} integrations. "
                "Upgrade to connect more."
            ),
            "upgrade_url": "/contact",
        },
    )


def resolve_inbound_tenant() -> str:
    """Tenant for unauthenticated inbound webhooks (Twilio, Meta, email)."""
    settings = get_settings()
    return (settings.default_webhook_tenant_id or settings.oidc_default_tenant_id or "default").strip()


def require_inbound_channel(channel: str) -> str:
    """Gate inbound webhook channel and return resolved tenant_id."""
    tenant_id = resolve_inbound_tenant()
    require_channel(tenant_id, channel)
    return tenant_id


def agent_channel(agent_id: str) -> str:
    agents = load_agent_config().get("agents", {})
    cfg = agents.get(agent_id, {})
    return str(cfg.get("channel", "chat"))
