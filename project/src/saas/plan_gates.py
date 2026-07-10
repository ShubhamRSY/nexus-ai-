"""Plan-based feature gates for Nexus Cloud tiers."""

from __future__ import annotations

from fastapi import HTTPException

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
}


def tenant_plan_id(tenant_id: str) -> str:
    sub = db.get_tenant_subscription(tenant_id)
    return (sub or {}).get("plan_id") or "free"


def plan_allows_channel(tenant_id: str, channel: str) -> bool:
    plan = get_plan(tenant_plan_id(tenant_id)) or get_plan("free")
    allowed = {c.lower() for c in plan.get("channels", [])}
    return _CHANNEL_ALIASES.get(channel.lower(), channel.lower()) in allowed


def require_channel(tenant_id: str, channel: str) -> None:
    if plan_allows_channel(tenant_id, channel):
        return
    plan = get_plan(tenant_plan_id(tenant_id)) or get_plan("free")
    raise HTTPException(
        status_code=402,
        detail={
            "code": "plan_upgrade_required",
            "message": f"{channel.title()} is not included on the {plan['name']} plan. Upgrade to unlock.",
            "upgrade_url": "/contact",
        },
    )
