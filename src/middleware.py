"""Middleware for rate limiting, tenant resolution, and request logging."""

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.cache import get_cache
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
        self.cache = get_cache()
        self.rpm = rpm

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
        
        # Use a more general key for endpoint groups
        endpoint_group = next((p for p in self._ENDPOINT_LIMITS if request.url.path.startswith(p)), "default")
        key = f"rate_limit:{tenant_id}:{client_ip}:{endpoint_group}"
        limit = self._get_limit(request.url.path)

        now = time.time()
        
        # This requires an async Redis client. We'll use the one from cache.
        if not hasattr(self.cache, "_get_client"):
            logger.warning("rate_limiter_unsupported_cache", backend=type(self.cache).__name__)
            return await call_next(request)

        client = self.cache._get_client()
        if not client:
            return await call_next(request)

        await client.zremrangebyscore(key, 0, now - 60)
        request_count = await client.zcard(key)

        if request_count >= limit:
            logger.warning("rate_limit_exceeded", key=key, limit=limit, count=request_count)
            return Response(status_code=429, content="Rate limit exceeded. Try again soon.")

        await client.zadd(key, {str(now): now})
        await client.expire(key, 60)
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
