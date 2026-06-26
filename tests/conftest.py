import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Override HF cache before any model imports
os.environ["HF_HOME"] = "/tmp/hf_cache_test"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "/tmp/hf_cache_test"


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    """Ensure tests run in offline mock mode without external LLM calls."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    from src.config import reload_settings

    reload_settings()
