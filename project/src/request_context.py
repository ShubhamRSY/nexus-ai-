"""Per-request context for agent tools (session, tenant)."""

from contextvars import ContextVar

_session_id: ContextVar[str] = ContextVar("session_id", default="")
_tenant_id: ContextVar[str] = ContextVar("tenant_id", default="default")


def set_request_context(*, session_id: str = "", tenant_id: str = "default") -> None:
    _session_id.set(session_id)
    _tenant_id.set(tenant_id)


def get_request_session_id() -> str:
    return _session_id.get()


def get_request_tenant_id() -> str:
    return _tenant_id.get()
