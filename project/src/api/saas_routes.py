"""Public Nexus Cloud sign-up, billing, and provisioning."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from structlog import get_logger

from src.auth import AuthContext, hash_password, require_auth
from src.config import get_settings
from src.database import db
from src.saas import billing
from src.saas.provisioning import SAAS_PLANS, get_plan, provision_workspace

logger = get_logger()
router = APIRouter()


class SaasSignupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    admin_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)
    plan_id: str = Field(min_length=1)
    accept_terms: bool = False


class SubscribeRequest(BaseModel):
    plan_id: str = Field(min_length=1)


@router.get("/saas/signup/config")
async def signup_config() -> dict:
    settings = get_settings()
    return {
        "enabled": settings.saas_signup_enabled,
        "plans": SAAS_PLANS,
        "stripe_checkout": billing.is_configured(),
        "trial_days_default": 14,
        "signup_url": f"{settings.app_public_url.rstrip('/')}/signup",
        "hosted_region": settings.primary_region,
    }


@router.post("/saas/signup")
async def saas_signup(body: SaasSignupRequest) -> dict[str, Any]:
    """Provision a new workspace on Nexus Cloud (shared multi-tenant hosting)."""
    settings = get_settings()
    if not settings.saas_signup_enabled:
        raise HTTPException(status_code=403, detail="SaaS signup is disabled")

    if not body.accept_terms:
        raise HTTPException(status_code=400, detail="You must accept the Terms of Service and Privacy Policy")

    if not get_plan(body.plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan")

    plan = get_plan(body.plan_id)
    if plan and plan.get("contact_sales"):
        raise HTTPException(status_code=400, detail="Contact sales for Enterprise — see /contact")

    if db.get_user_by_email(str(body.email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    pw_hash = hash_password(body.password)

    if billing.is_configured():
        try:
            checkout = await billing.create_checkout_session(
                email=str(body.email),
                company_name=body.company_name,
                admin_name=body.admin_name,
                password_hash=pw_hash,
                plan_id=body.plan_id,
            )
            return {
                "status": "checkout_required",
                "checkout_url": checkout["checkout_url"],
                "pending_id": checkout["pending_id"],
                "message": "Complete payment to activate your workspace.",
            }
        except Exception as exc:
            logger.error("saas_checkout_failed", error=str(exc))
            raise HTTPException(status_code=502, detail="Payment setup failed") from exc

    try:
        result = provision_workspace(
            company_name=body.company_name,
            admin_name=body.admin_name,
            email=str(body.email),
            password_hash=pw_hash,
            plan_id=body.plan_id,
            status="trialing",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    subscription_status = result.pop("status", "trialing")
    return {
        "status": "provisioned",
        "subscription_status": subscription_status,
        "message": "Your workspace is ready.",
        **result,
    }


@router.get("/saas/signup/status")
async def signup_status(pending_id: str) -> dict:
    pending = db.get_signup_pending(pending_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Signup session not found")
    return {
        "pending_id": pending_id,
        "completed": pending.get("completed", False),
        "email": pending.get("email"),
        "plan_id": pending.get("plan_id"),
    }


@router.post("/saas/webhooks/stripe")
async def stripe_webhook(request: Request) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not billing.verify_webhook_signature(payload, sig):
        raise HTTPException(status_code=400, detail="Invalid signature")
    import json
    event = json.loads(payload)
    return await billing.handle_webhook_event(event)


@router.get("/saas/plans")
async def list_plans() -> dict:
    settings = get_settings()
    return {
        "plans": SAAS_PLANS,
        "hosted": True,
        "signup": f"{settings.app_public_url.rstrip('/')}/signup",
    }


@router.get("/saas/subscription")
async def get_subscription(ctx: AuthContext = Depends(require_auth)) -> dict:
    return {"subscription": db.get_tenant_subscription(ctx.tenant_id), "plans": SAAS_PLANS}


@router.post("/saas/subscribe")
async def change_plan(body: SubscribeRequest, ctx: AuthContext = Depends(require_auth)) -> dict:
    if not ctx.is_admin():
        raise HTTPException(status_code=403, detail="Admin required")
    if not get_plan(body.plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan")
    sub = db.set_tenant_subscription(ctx.tenant_id, body.plan_id)
    db.log_audit(ctx.tenant_id, ctx.user_id, "saas.subscribe", "subscription", {"plan_id": body.plan_id})
    return {"status": "subscribed", "subscription": sub}
