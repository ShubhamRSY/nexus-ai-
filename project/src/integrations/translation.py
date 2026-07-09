"""Language detection and translation for omnichannel CX."""

from __future__ import annotations

import re

import structlog

from src.config import get_settings

logger = structlog.get_logger()

_LANG_HINTS: dict[str, re.Pattern[str]] = {
    "es": re.compile(r"\b(hola|gracias|por favor|ayuda|cuenta|problema)\b", re.I),
    "fr": re.compile(r"\b(bonjour|merci|s'il vous plaît|aide|compte|problème)\b", re.I),
    "de": re.compile(r"\b(hallo|danke|bitte|hilfe|konto|problem)\b", re.I),
    "pt": re.compile(r"\b(olá|obrigado|por favor|ajuda|conta|problema)\b", re.I),
}


def detect_locale(text: str, fallback: str = "en") -> str:
    """Lightweight locale guess from common words; defaults to English."""
    sample = (text or "").strip()
    if not sample:
        return fallback
    if re.search(r"[\u4e00-\u9fff]", sample):
        return "zh"
    if re.search(r"[\u0600-\u06ff]", sample):
        return "ar"
    for code, pattern in _LANG_HINTS.items():
        if pattern.search(sample):
            return code
    return fallback


async def translate_text(text: str, target_locale: str = "en", source_locale: str | None = None) -> dict:
    """Translate text using the configured LLM; passthrough when unavailable."""
    cleaned = (text or "").strip()
    if not cleaned:
        return {"text": "", "source_locale": source_locale or "en", "target_locale": target_locale}

    src = source_locale or detect_locale(cleaned)
    if src == target_locale:
        return {"text": cleaned, "source_locale": src, "target_locale": target_locale}

    settings = get_settings()
    if not settings.openai_api_key:
        logger.info("translation_passthrough", source=src, target=target_locale)
        return {"text": cleaned, "source_locale": src, "target_locale": target_locale, "mode": "passthrough"}

    try:
        import httpx

        prompt = (
            f"Translate the following customer message from {src} to {target_locale}. "
            "Return only the translation, no quotes or explanation.\n\n"
            f"{cleaned}"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.default_llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 800,
                },
            )
            resp.raise_for_status()
            translated = resp.json()["choices"][0]["message"]["content"].strip()
            return {
                "text": translated,
                "source_locale": src,
                "target_locale": target_locale,
                "mode": "llm",
            }
    except Exception as exc:
        logger.warning("translation_failed", error=str(exc))
        return {"text": cleaned, "source_locale": src, "target_locale": target_locale, "mode": "fallback"}


async def localize_response(text: str, target_locale: str) -> str:
    """Translate an English agent response back to the customer's locale."""
    if not target_locale or target_locale == "en":
        return text
    result = await translate_text(text, target_locale=target_locale, source_locale="en")
    return result["text"]
