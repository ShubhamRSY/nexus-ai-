"""Multi-region HA readiness and failover helpers."""

from __future__ import annotations

import time

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class RegionHealth:
    def snapshot(self) -> dict:
        settings = get_settings()
        return {
            "primary_region": settings.primary_region,
            "secondary_region": settings.secondary_region,
            "failover_enabled": settings.ha_failover_enabled,
            "read_replica_url_configured": bool(settings.database_read_replica_url),
            "timestamp": time.time(),
        }

    async def check_peer(self) -> dict:
        settings = get_settings()
        peer = settings.ha_peer_health_url.strip()
        if not peer:
            return {"peer": None, "status": "not_configured"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(peer)
                return {"peer": peer, "status": "healthy" if resp.status_code == 200 else "degraded", "code": resp.status_code}
        except Exception as exc:
            logger.warning("ha_peer_check_failed", error=str(exc))
            return {"peer": peer, "status": "unreachable", "error": str(exc)}

    def active_database_url(self) -> str:
        settings = get_settings()
        if settings.ha_failover_enabled and settings.database_read_replica_url:
            return settings.database_url or ""
        return settings.database_url or ""


region_health = RegionHealth()
