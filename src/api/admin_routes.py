"""Admin-only routes: user management."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from structlog import get_logger

from src.auth import AuthContext, hash_password, require_admin
from src.database import db

logger = get_logger()
router = APIRouter()


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3)
    name: str = Field(min_length=1)
    password: str = Field(min_length=8)
    role: str = Field("agent", description="agent|admin")


@router.post("/admin/users")
async def create_user(body: CreateUserRequest, ctx: AuthContext = Depends(require_admin)) -> dict[str, Any]:
    if body.role not in ("agent", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = f"user-{uuid.uuid4().hex[:8]}"
    db.create_user(
        user_id=user_id,
        tenant_id=ctx.tenant_id,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        role=body.role,
    )
    db.log_audit(
        ctx.tenant_id,
        ctx.user_id,
        "admin.user.created",
        "user",
        {"created_user_id": user_id, "email": body.email, "role": body.role},
    )

    return {"status": "created", "user_id": user_id, "email": body.email, "role": body.role}

