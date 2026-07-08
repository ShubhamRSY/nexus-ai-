"""Twilio webhook signature validation."""

from fastapi import HTTPException, Request
from structlog import get_logger
from twilio.request_validator import RequestValidator

from src.config import get_settings

logger = get_logger()


def _twilio_validation_url(request: Request) -> str:
    """Build the public URL Twilio signed (may differ behind a reverse proxy)."""
    settings = get_settings()
    base = settings.twilio_webhook_base_url.rstrip("/")
    path = request.url.path
    query = request.url.query
    if query:
        return f"{base}{path}?{query}"
    return f"{base}{path}"


async def require_twilio_signature(request: Request) -> None:
    """Validate X-Twilio-Signature on inbound webhook requests.

    Skipped when TWILIO_AUTH_TOKEN is not configured (local development).
    """
    settings = get_settings()
    auth_token = settings.twilio_auth_token.strip()
    if not auth_token:
        logger.debug("twilio_signature_skipped", reason="no_auth_token_configured")
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    url = _twilio_validation_url(request)
    validator = RequestValidator(auth_token)

    if not validator.validate(url, params, signature):
        logger.warning("twilio_signature_invalid", url=url)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
