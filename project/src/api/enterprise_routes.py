"""Enterprise contact-center features: agent status, IVR, supervisor, QM, cobrowse, SaaS."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from structlog import get_logger

from src.database import db
from src.ha.region import region_health
from src.api.deps import require_auth

logger = get_logger()
router = APIRouter()


class AgentStatusRequest(BaseModel):
    status: str = Field(pattern="^(available|away|break|offline)$")
    skills: str = ""


class IvrFlowRequest(BaseModel):
    name: str = Field(min_length=1)
    nodes: list = Field(default_factory=list)
    edges: list = Field(default_factory=list)
    entry_node: str = "start"
    active: bool = False
    id: int | None = None


class QmReviewRequest(BaseModel):
    session_id: str
    overall_score: int = Field(ge=1, le=5)
    rubric: dict = Field(default_factory=dict)
    notes: str = ""
    status: str = "completed"


class SupervisorRequest(BaseModel):
    session_id: str
    mode: str = Field(pattern="^(monitor|whisper|barge)$")
    message: str = ""


class CobrowseStartRequest(BaseModel):
    customer_token: str = Field(min_length=4)


# --- Multi-region HA ---
@router.post("/agents/status")
async def set_agent_status(body: AgentStatusRequest, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    result = db.set_agent_status(ctx.user_id, tenant_id, body.status, body.skills)
    return {"status": "updated", "presence": result}


@router.get("/agents/team")
async def get_team_status(ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    team = db.get_team_presence(tenant_id)
    return {"team": team, "count": len(team)}


# --- IVR designer ---
@router.get("/ivr/flows")
async def list_ivr_flows(ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    return {"flows": db.list_ivr_flows(tenant_id)}


@router.post("/ivr/flows")
async def save_ivr_flow(body: IvrFlowRequest, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    flow = db.save_ivr_flow(tenant_id, body.name, body.nodes, body.edges, body.entry_node, body.id, body.active)
    return {"status": "saved", "flow": flow}


# --- Supervisor ---
@router.post("/supervisor/action")
async def supervisor_action(body: SupervisorRequest, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    action = db.log_supervisor_action(body.session_id, tenant_id, ctx.user_id, body.mode, body.message)
    if body.mode == "whisper" and body.message:
        db.save_message(body.session_id, "supervisor", f"[Whisper to agent] {body.message}")
    elif body.mode == "barge" and body.message:
        db.save_message(body.session_id, "supervisor", body.message)
    return {"status": "ok", "action": action}


@router.get("/supervisor/actions/{session_id}")
async def list_supervisor_actions(session_id: str, ctx: Any = Depends(require_auth)) -> dict:
    return {"actions": db.list_supervisor_actions(session_id)}


# --- Quality management ---
@router.get("/qm/reviews")
async def list_qm_reviews(status: str | None = None, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    return {"reviews": db.list_qm_reviews(tenant_id, status)}


@router.post("/qm/reviews")
async def create_qm_review(body: QmReviewRequest, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    review = db.create_qm_review(
        body.session_id, tenant_id, ctx.user_id, body.overall_score, body.rubric, body.notes, body.status,
    )
    return {"status": "recorded", "review": review}


@router.get("/qm/pending")
async def qm_pending_queue(ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    sessions = db.list_inbox(tenant_id)
    reviewed_ids = {r["session_id"] for r in db.list_qm_reviews(tenant_id)}
    pending = [s for s in sessions if s["id"] not in reviewed_ids]
    return {"pending": pending[:50], "count": len(pending)}


# --- Co-browsing ---
@router.post("/cobrowse/start")
async def start_cobrowse(body: CobrowseStartRequest, ctx: Any = Depends(require_auth)) -> dict:
    tenant_id = ctx.tenant_id if ctx else "default"
    sid = f"cb-{uuid.uuid4().hex[:12]}"
    session = db.create_cobrowse_session(sid, tenant_id, body.customer_token)
    return {"status": "waiting", "session": session, "join_url": f"/api/v1/cobrowse/ws/{sid}"}


@router.post("/cobrowse/{session_id}/join")
async def join_cobrowse(session_id: str, ctx: Any = Depends(require_auth)) -> dict:
    session = db.join_cobrowse(session_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Co-browse session not found")
    return {"status": "active", "session": session}


_cobrowse_rooms: dict[str, set] = {}


@router.websocket("/cobrowse/ws/{session_id}")
async def cobrowse_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    _cobrowse_rooms.setdefault(session_id, set()).add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for peer in list(_cobrowse_rooms.get(session_id, set())):
                if peer is not websocket:
                    await peer.send_text(data)
    except WebSocketDisconnect:
        pass
    finally:
        _cobrowse_rooms.get(session_id, set()).discard(websocket)


# --- Multi-region HA ---
@router.get("/ha/status")
async def ha_status() -> dict:
    peer = await region_health.check_peer()
    return {"region": region_health.snapshot(), "peer": peer}
