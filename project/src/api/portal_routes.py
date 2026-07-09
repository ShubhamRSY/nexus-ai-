"""Customer self-service portal API — KB search and ticket tracking."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from structlog import get_logger

from src.database import db
from src.rag.retriever import KnowledgeRetriever

logger = get_logger()
router = APIRouter()

_retriever: KnowledgeRetriever | None = None


def _get_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


class PortalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    tenant_id: str = "default"


class PortalTicketCreate(BaseModel):
    email: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    description: str = ""
    tenant_id: str = "default"


class PortalTicketLookup(BaseModel):
    ticket_id: int
    email: str
    tenant_id: str = "default"


class CobrowseStartRequest(BaseModel):
    customer_token: str = Field(min_length=4)


@router.get("/portal")
async def portal_info() -> dict:
    return {
        "name": "Nexus Customer Portal",
        "ui": "/portal",
        "features": ["kb_search", "ticket_submit", "ticket_track", "cobrowse_start"],
    }


@router.post("/portal/kb/search")
async def portal_kb_search(body: PortalSearchRequest) -> dict:
    context = _get_retriever().format_context(body.query)
    articles = db.list_articles(body.tenant_id)
    matched = [a for a in articles if body.query.lower() in (a.get("title", "") + a.get("content", "")).lower()][:5]
    return {"query": body.query, "context": context, "articles": matched}


@router.post("/portal/tickets")
async def portal_create_ticket(body: PortalTicketCreate) -> dict:
    ticket = db.create_ticket(body.tenant_id, body.subject, body.description, customer_id=body.email)
    logger.info("portal_ticket_created", ticket_id=ticket.get("id"), email=body.email)
    return {"status": "created", "ticket": ticket}


@router.post("/portal/tickets/lookup")
async def portal_ticket_lookup(body: PortalTicketLookup) -> dict:
    ticket = db.portal_lookup_ticket(body.tenant_id, body.ticket_id, body.email)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found for this email")
    return {"ticket": ticket}


@router.get("/portal/tickets/{ticket_id}")
async def portal_ticket_status(ticket_id: int, email: str, tenant_id: str = "default") -> dict:
    ticket = db.portal_lookup_ticket(tenant_id, ticket_id, email)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"ticket": ticket}


@router.post("/portal/cobrowse/start")
async def portal_cobrowse_start(body: CobrowseStartRequest) -> dict:
    import uuid
    tenant_id = "default"
    sid = f"cb-{uuid.uuid4().hex[:12]}"
    session = db.create_cobrowse_session(sid, tenant_id, body.customer_token)
    return {"status": "waiting", "session": session, "join_url": f"/api/v1/cobrowse/ws/{sid}"}
