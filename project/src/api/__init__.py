"""REST API layer — routers split by domain for maintainability."""

from src.api.auth_routes import router as auth_router
from src.api.chat_routes import router as chat_router
from src.api.kb_routes import router as kb_router
from src.api.telephony_routes import router as telephony_router
from src.api.integration_routes import router as integration_router
from src.api.ops_routes import router as ops_router
from src.api.session_manager import SessionManager

__all__ = [
    "auth_router", "chat_router", "kb_router",
    "telephony_router", "integration_router", "ops_router",
    "SessionManager",
]
