"""FastAPI routes for chat, voice, copilot, RAG, and evaluation."""

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.api.session_manager import SessionManager
from src.config import Settings, get_settings, reload_settings
from src.evaluation.evaluator import AgentEvaluator
from src.integrations.crm import CRMClient, HubSpotClient
from src.integrations.secrets_vault import CREDENTIAL_KEYS, WEBHOOK_EVENTS, get_secrets_vault
from src.integrations.webhooks import IntegrationRouter
from src.rag.ingestion import ingest_directory, ingest_file
from src.rag.vector_store import VectorStore
from src.telephony.call_router import CallMetadata, CallRouter, RoutingRule
from src.telephony.stt import transcribe_audio
from src.telephony.tts import DEFAULT_VOICE, synthesize_speech
from src.telephony.twilio_handler import TwilioVoiceHandler
from src.telephony.twiml_parser import parse_twiml
from src.workflows.orchestrator import AgentOrchestrator

logger = structlog.get_logger()
router = APIRouter()
integration_router = IntegrationRouter()
voice_handler = TwilioVoiceHandler()


class ChatRequest(BaseModel):
    message: str
    agent_id: str = "chat_support"
    customer_info: str = ""
    session_id: str = ""


class ChatResponse(BaseModel):
    response: str
    agent_id: str
    tool_calls: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)


class CopilotRequest(BaseModel):
    message: str
    conversation_summary: str = ""
    agent_id: str = "copilot"


class IngestRequest(BaseModel):
    source_path: str


class WebhookRegisterRequest(BaseModel):
    event_type: str
    url: str


class CredentialsUpdateRequest(BaseModel):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None
    twilio_webhook_base_url: str | None = None
    hubspot_api_key: str | None = None
    webhook_signing_secret: str | None = None


class VoiceSimulateRequest(BaseModel):
    call_sid: str = "SIM-CALL-001"
    from_number: str = "+15551234567"
    speech: str | None = None
    sip_headers: dict[str, str] = Field(default_factory=dict)


class SpeakRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE


_call_router = CallRouter()
_call_router.add_rule(RoutingRule("vip", "from:+1555", "+15559999999", priority=10))
_call_router.set_fallback("+15551111111")


_sessions = SessionManager(ttl_seconds=3600, max_sessions=1000)


def _get_session(session_id: str, agent_id: str) -> AgentOrchestrator:
    return _sessions.get(session_id, agent_id)


def _require_settings_token(request: Request) -> None:
    token = get_settings().settings_admin_token.strip()
    if not token:
        return
    provided = request.headers.get("X-Settings-Token", "")
    if provided != token:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Settings-Token header.")


def _env_credentials() -> dict[str, str]:
    env_settings = Settings()
    return {key: getattr(env_settings, key, "") or "" for key in CREDENTIAL_KEYS}


@router.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "enterprise-voice-agents",
        "stt_available": bool(settings.openai_api_key),
        "tts_available": bool(settings.openai_api_key),
        "tts_voice": DEFAULT_VOICE,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or "default"
    orchestrator = _get_session(session_id, request.agent_id)

    result = await orchestrator.invoke(
        user_input=request.message,
        customer_info=request.customer_info or "No customer identified",
    )

    await integration_router.on_conversation_start(session_id, "chat", {
        "agent_id": request.agent_id,
    })

    return ChatResponse(
        response=result["response"],
        agent_id=result["agent_id"],
        tool_calls=result.get("tool_calls", []),
        metrics=result.get("metrics", {}),
    )


@router.post("/copilot")
async def copilot(request: CopilotRequest) -> dict[str, Any]:
    orchestrator = AgentOrchestrator(request.agent_id)
    result = await orchestrator.invoke(
        user_input=request.message,
        extra_context=request.conversation_summary,
    )
    return result


@router.delete("/chat/{session_id}")
async def end_session(session_id: str) -> dict[str, str]:
    _sessions.remove(session_id)
    await integration_router.on_conversation_end(session_id, "completed", {})
    return {"status": "session_ended"}


@router.get("/sessions/stats")
async def session_stats() -> dict[str, int]:
    """Expose active session count for observability."""
    _sessions.evict_stale()
    return {"active_sessions": _sessions.active_count}


@router.post("/rag/ingest")
async def ingest_documents(request: IngestRequest) -> dict[str, Any]:
    from pathlib import Path

    path = Path(request.source_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    if path.is_dir():
        count = ingest_directory(path)
    else:
        count = ingest_file(path)

    return {"ingested_chunks": count, "source": str(path)}


@router.post("/rag/search")
async def search_knowledge(query: str, top_k: int = 5) -> dict[str, Any]:
    store = VectorStore()
    results = store.similarity_search(query, k=top_k)
    return {"query": query, "results": results}


@router.post("/telephony/voice/inbound")
async def voice_inbound(request: Request):
    return await voice_handler.handle_inbound(request)


@router.post("/telephony/voice/process")
async def voice_process(request: Request):
    return await voice_handler.handle_process(request)


@router.post("/telephony/voice/status")
async def voice_status(request: Request) -> dict[str, Any]:
    return await voice_handler.handle_status_callback(request)


@router.post("/telephony/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)) -> dict[str, str]:
    """Transcribe caller speech audio via OpenAI Whisper."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Server transcription requires OPENAI_API_KEY. Type caller speech and tap Send.",
        )

    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio recording.")

    text = await asyncio.to_thread(
        transcribe_audio,
        content,
        audio.filename or "speech.webm",
    )
    if not text:
        raise HTTPException(status_code=422, detail="Could not transcribe audio. Speak longer and try again.")

    return {"text": text}


@router.post("/telephony/speak")
async def speak_agent(request: SpeakRequest) -> Response:
    """Synthesize agent voice audio (OpenAI TTS — warm female voice)."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="TTS requires OPENAI_API_KEY.")

    audio = await asyncio.to_thread(synthesize_speech, request.text, request.voice)
    if not audio:
        raise HTTPException(status_code=400, detail="Nothing to speak.")

    return Response(content=audio, media_type="audio/mpeg")


@router.post("/telephony/simulate")
async def telephony_simulate(request: VoiceSimulateRequest) -> dict[str, Any]:
    """Simulate PSTN/CCaaS voice call flow without Twilio credentials."""
    sip_meta = _call_router.extract_sip_headers(request.sip_headers)
    metadata = CallMetadata(
        call_sid=request.call_sid,
        from_number=request.from_number,
        to_number="+1800ACME",
        custom_fields=sip_meta,
    )
    route_destination = _call_router.route(metadata)

    twiml = await voice_handler.simulate(
        call_sid=request.call_sid,
        from_number=request.from_number,
        speech_result=request.speech,
    )
    parsed = parse_twiml(twiml)

    return {
        "call_sid": request.call_sid,
        "from_number": request.from_number,
        "caller_said": request.speech,
        "agent_says": parsed["agent_says"],
        "agent_response": parsed.get("agent_response", ""),
        "spoken_responses": parsed["spoken_responses"],
        "transfer_to": parsed["transfer_to"],
        "listening": parsed["listening"],
        "call_actions": parsed["actions"],
        "routing": {
            "destination": route_destination,
            "sip_headers": sip_meta,
            "strategy": "skill_based",
        },
        "twiml": twiml,
    }


@router.post("/integrations/webhooks")
async def register_webhook(request: Request, body: WebhookRegisterRequest) -> dict[str, str]:
    _require_settings_token(request)
    if body.event_type not in WEBHOOK_EVENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported event type: {body.event_type}")
    integration_router.register_webhook(body.event_type, body.url)
    return {"status": "registered", "event_type": body.event_type}


@router.delete("/integrations/webhooks/{event_type}")
async def delete_webhook(request: Request, event_type: str) -> dict[str, str]:
    _require_settings_token(request)
    if event_type not in WEBHOOK_EVENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported event type: {event_type}")
    integration_router.unregister_webhook(event_type)
    return {"status": "removed", "event_type": event_type}


@router.get("/integrations/status")
async def integrations_status() -> dict[str, Any]:
    settings = get_settings()
    vault = get_secrets_vault()
    creds = vault.credential_status(_env_credentials())
    hooks = vault.webhook_status()

    return {
        "encryption": {
            "enabled": vault.path.exists(),
            "vault_path": str(vault.path),
            "key_source": "env" if settings.integrations_encryption_key else "local_file",
        },
        "providers": {
            "openai": {
                "configured": creds["openai_api_key"]["configured"],
                "source": creds["openai_api_key"]["source"],
                "masked_key": creds["openai_api_key"]["masked"],
                "features": ["llm", "embeddings", "stt", "tts"],
            },
            "anthropic": {
                "configured": creds["anthropic_api_key"]["configured"],
                "source": creds["anthropic_api_key"]["source"],
                "masked_key": creds["anthropic_api_key"]["masked"],
                "features": ["llm"],
            },
            "twilio": {
                "configured": all(
                    creds[key]["configured"]
                    for key in ("twilio_account_sid", "twilio_auth_token", "twilio_phone_number")
                ),
                "masked_sid": creds["twilio_account_sid"]["masked"],
                "masked_phone": creds["twilio_phone_number"]["masked"],
                "webhook_base_url": creds["twilio_webhook_base_url"]["masked"] or None,
                "source": "vault" if vault.get_credentials().get("twilio_account_sid") else (
                    "env" if _env_credentials().get("twilio_account_sid") else "none"
                ),
                "features": ["pstn", "voice_webhooks"],
            },
            "hubspot": {
                "configured": creds["hubspot_api_key"]["configured"],
                "source": creds["hubspot_api_key"]["source"],
                "masked_key": creds["hubspot_api_key"]["masked"],
                "features": ["crm_lookup", "ticket_sync"],
            },
            "ipaas": {
                "configured": any(item["configured"] for item in hooks.values()),
                "webhook_signing": creds["webhook_signing_secret"]["configured"],
                "masked_signing_secret": creds["webhook_signing_secret"]["masked"],
                "events": hooks,
                "features": ["n8n", "zapier"],
            },
        },
        "mock_mode": not bool(settings.openai_api_key or settings.anthropic_api_key),
    }


@router.put("/integrations/credentials")
async def save_credentials(request: Request, body: CredentialsUpdateRequest) -> dict[str, Any]:
    _require_settings_token(request)
    vault = get_secrets_vault()
    updates = body.model_dump(exclude_unset=True)
    vault.set_credentials(updates)
    reload_settings()
    integration_router.load_from_vault()
    return {
        "status": "saved",
        "updated": list(updates.keys()),
        "providers": (await integrations_status())["providers"],
    }


@router.delete("/integrations/credentials/{credential_key}")
async def delete_credential(request: Request, credential_key: str) -> dict[str, str]:
    _require_settings_token(request)
    if credential_key not in CREDENTIAL_KEYS:
        raise HTTPException(status_code=400, detail=f"Unsupported credential: {credential_key}")
    get_secrets_vault().clear_credential(credential_key)
    reload_settings()
    integration_router.load_from_vault()
    return {"status": "cleared", "credential": credential_key}


@router.post("/evaluation/run")
async def run_evaluation() -> dict[str, Any]:
    from src.config import EVALUATION_DIR

    evaluator = AgentEvaluator(str(EVALUATION_DIR / "test_cases.json"))
    return await evaluator.run_suite()


@router.get("/agents")
async def list_agents() -> dict[str, Any]:
    from src.config import load_agent_config
    from src.llm.params import resolve_llm_params

    config = load_agent_config()
    defaults = config.get("llm_defaults", {})
    return {
        agent_id: {
            "name": cfg["name"],
            "channel": cfg["channel"],
            "tools": cfg.get("tools", []),
            "llm_params": resolve_llm_params(cfg, defaults),
        }
        for agent_id, cfg in config["agents"].items()
    }


@router.get("/llm/config")
async def get_llm_config() -> dict[str, Any]:
    """Return user-configurable LLM parameters per agent."""
    from src.config import load_agent_config
    from src.llm.params import DEFAULT_LLM_PARAMS, resolve_llm_params

    config = load_agent_config()
    return {
        "defaults": DEFAULT_LLM_PARAMS,
        "global": config.get("llm_defaults", {}),
        "guardrails": config.get("guardrails", {}),
        "agents": {
            agent_id: resolve_llm_params(cfg, config.get("llm_defaults"))
            for agent_id, cfg in config["agents"].items()
        },
    }
