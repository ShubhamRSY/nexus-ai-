"""Middleware for rate limiting, tenant resolution, and request logging."""

import time
from collections import defaultdict

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.auth import decode_jwt

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter with per-endpoint-group limits (per-IP, per-tenant)."""

    _ENDPOINT_LIMITS: dict[str, int] = {
        "/api/v1/chat": 30,
        "/api/v1/copilot": 20,
        "/api/v1/telephony": 15,
        "/api/v1/evaluation": 10,
        "/api/v1/rag": 30,
        "/api/v1/messaging": 20,
    }
    _DEFAULT_LIMIT = 60

    def __init__(self, app: ASGIApp, rpm: int = 60):
        super().__init__(app)
        self._windows: dict[str, list[float]] = defaultdict(list)

    def _get_limit(self, path: str) -> int:
        for prefix, limit in self._ENDPOINT_LIMITS.items():
            if path.startswith(prefix):
                return limit
        return self._DEFAULT_LIMIT

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = "public"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_jwt(auth_header[7:])
            if payload:
                tenant_id = payload.get("tenant_id", "public")

        key = f"{tenant_id}:{client_ip}:{request.url.path}"
        limit = self._get_limit(request.url.path)

        now = time.time()
        window = self._windows[key]
        cutoff = now - 60
        while window and window[0] < cutoff:
            window.pop(0)

        if len(window) >= limit:
            logger.warning("rate_limit_exceeded", key=key, limit=limit, count=len(window))
            return Response(status_code=429, content="Rate limit exceeded. Try again soon.")

        window.append(now)
        return await call_next(request)


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolve tenant from JWT or subdomain and attach to request state."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = "default"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_jwt(auth_header[7:])
            if payload:
                tenant_id = payload.get("tenant_id", "default")

        request.state.tenant_id = tenant_id
        return await call_next(request)
