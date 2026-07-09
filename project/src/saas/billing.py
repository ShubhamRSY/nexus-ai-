"""Stripe Checkout for Nexus Cloud (optional — uses REST, no SDK required)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import httpx
import structlog

from src.config import get_settings
from src.database import db
from src.saas.provisioning import get_plan, provision_workspace

logger = structlog.get_logger()

STRIPE_API = "https://api.stripe.com/v1"


def is_configured() -> bool:
    return bool(get_settings().stripe_secret_key.strip())


async def create_checkout_session(
    *,
    email: str,
    company_name: str,
    admin_name: str,
    password_hash: str,
    plan_id: str,
) -> dict:
    settings = get_settings()
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError("Invalid plan")

    pending_id = f"signup-{uuid.uuid4().hex[:12]}"
    db.save_signup_pending(pending_id, email, company_name, admin_name, password_hash, plan_id)

    success_url = f"{settings.app_public_url.rstrip('/')}/signup?success=1&pending={pending_id}"
    cancel_url = f"{settings.app_public_url.rstrip('/')}/signup?canceled=1"

    amount_cents = int(plan["price_monthly"]) * 100
    data = {
        "mode": "subscription",
        "customer_email": email,
        "client_reference_id": pending_id,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata[pending_id]": pending_id,
        "metadata[plan_id]": plan_id,
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][product_data][name]": f"Nexus Cloud — {plan['name']}",
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][recurring][interval]": "month",
        "line_items[0][quantity]": "1",
        "subscription_data[trial_period_days]": str(plan.get("trial_days", 14)),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{STRIPE_API}/checkout/sessions",
            auth=(settings.stripe_secret_key, ""),
            data=data,
        )
    if resp.status_code not in (200, 201):
        logger.error("stripe_checkout_failed", status=resp.status_code, body=resp.text[:300])
        raise RuntimeError("Payment provider error")

    session = resp.json()
    db.update_signup_pending_stripe(pending_id, session.get("id", ""))
    return {"checkout_url": session["url"], "session_id": session["id"], "pending_id": pending_id}


def verify_webhook_signature(payload: bytes, signature_header: str) -> bool:
    secret = get_settings().stripe_webhook_secret
    if not secret:
        return True
    parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
    timestamp = parts.get("t", "")
    sig = parts.get("v1", "")
    if not timestamp or not sig:
        return False
    signed = f"{timestamp}.{payload.decode()}"
    expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


async def handle_webhook_event(event: dict) -> dict:
    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    if etype == "checkout.session.completed":
        pending_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("pending_id", "")
        pending = db.get_signup_pending(pending_id)
        if not pending:
            logger.warning("stripe_webhook_pending_missing", pending_id=pending_id)
            return {"status": "ignored"}
        if pending.get("completed"):
            return {"status": "already_completed"}

        result = provision_workspace(
            company_name=pending["company_name"],
            admin_name=pending["admin_name"],
            email=pending["email"],
            password_hash=pending["password_hash"],
            plan_id=pending["plan_id"],
            status="active",
            stripe_customer_id=str(obj.get("customer", "")),
            stripe_subscription_id=str(obj.get("subscription", "")),
        )
        db.complete_signup_pending(pending_id)
        return {"status": "provisioned", "tenant_id": result["tenant_id"]}

    if etype == "customer.subscription.deleted":
        sub_id = obj.get("id", "")
        db.update_subscription_by_stripe(sub_id, status="canceled")
        return {"status": "subscription_canceled"}

    return {"status": "ignored", "type": etype}
