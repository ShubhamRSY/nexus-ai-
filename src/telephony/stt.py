"""Speech-to-text for voice channel input."""

from io import BytesIO
from pathlib import Path

import structlog
from openai import OpenAI

from src.config import get_settings

logger = structlog.get_logger()


def transcribe_audio(content: bytes, filename: str = "speech.webm") -> str:
    """Transcribe audio bytes with OpenAI Whisper. Returns empty string if unavailable."""
    settings = get_settings()
    if not settings.openai_api_key:
        return ""

    suffix = Path(filename).suffix.lower() or ".webm"
    if suffix not in {".webm", ".mp4", ".m4a", ".mp3", ".wav", ".ogg", ".mpeg", ".mpga"}:
        suffix = ".webm"

    client = OpenAI(api_key=settings.openai_api_key)
    audio_file = BytesIO(content)
    audio_file.name = f"speech{suffix}"

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )

    text = (result.text or "").strip()
    logger.info("stt_transcribed", chars=len(text), suffix=suffix)
    return text
