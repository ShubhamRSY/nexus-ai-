"""Text-to-speech for voice agent responses."""

import structlog
from openai import OpenAI

from src.config import get_settings

logger = structlog.get_logger()

# shimmer = warm expressive female; nova = friendly bright female
DEFAULT_VOICE = "shimmer"
DEFAULT_MODEL = "tts-1-hd"
DEFAULT_SPEED = 1.05


def synthesize_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = DEFAULT_SPEED,
) -> bytes:
    """Generate MP3 speech audio via OpenAI TTS."""
    settings = get_settings()
    if not settings.openai_api_key:
        return b""

    clean = text.strip()
    if not clean:
        return b""

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.audio.speech.create(
        model=DEFAULT_MODEL,
        voice=voice,
        input=clean,
        speed=speed,
        response_format="mp3",
    )

    audio_bytes = response.content
    logger.info("tts_synthesized", voice=voice, chars=len(clean), bytes=len(audio_bytes))
    return audio_bytes
