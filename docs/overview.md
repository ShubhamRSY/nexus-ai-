# Nexus Overview

> **Nexus** is an open-source, enterprise-grade omnichannel AI agent platform that unifies chat, copilot, and voice into a single orchestration runtime.

---

## Architecture

Nexus follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                  Console (Web UI)                │
│    HTML/CSS/JS  ←  SSE Streaming  ←  REST API  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              FastAPI Application                 │
│    ┌────────┐ ┌──────────┐ ┌───────────────┐    │
│    │ Chat   │ │ Copilot  │ │ Voice         │    │
│    │ Router │ │ Router   │ │ Router        │    │
│    └───┬────┘ └────┬─────┘ └──────┬────────┘    │
│        │           │              │              │
│    ┌───▼───────────▼──────────────▼──────────┐  │
│    │           Orchestrator Layer            │  │
│    │   Session Mgr · Prompt Builder · Router │  │
│    └───┬───────────┬──────────────┬──────────┘  │
│        │           │              │              │
│    ┌───▼───┐ ┌────▼────┐ ┌───────▼───────┐     │
│    │  LLM  │ │  RAG    │ │  Feedback     │     │
│    │   ^   │ │  Engine │ │  Engine       │     │
│    │   │   │ │    ^    │ │    ^          │     │
│    └───┴───┘ └────┴────┘ └───────┴───────┘     │
│        │           │              │              │
│    ┌───▼───────────▼──────────────▼──────────┐  │
│    │           Infrastructure                │  │
│    │  Vault · DB · Twilio · Redis · Webhooks│  │
│    └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Message → REST → Orchestrator
  ├→ Session (create/load)
  ├→ RAG (retrieve context + citations)
  ├→ Prompt Builder (system prompt + history + context)
  ├→ LLM (streaming SSE response)
  └→ Response → Console
```

### Core Components

- **Chat Router** — `/api/v1/chat` — conversational AI with full session management
- **Copilot Router** — `/api/v1/copilot` — agent-assist for live agents (transcript → suggested reply)
- **Voice Router** — `/api/v1/voice` — PSTN telephony integration with Twilio/AWS Connect
- **Orchestrator** — session manager + prompt builder + agent router
- **RAG Engine** — vector-based retrieval augmented generation with source citations
- **Feedback Engine** — CSAT-driven auto-tuning of agent parameters
- **Vault** — AES-256-GCM encrypted credentials storage for integrations
- **iPaaS Webhooks** — lifecycle events (session.created, message.completed, feedback.submitted)

---

## API Reference

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message, get AI response |
| GET | `/api/v1/chat/stream/{session_id}` | SSE stream of chat messages |
| GET | `/api/v1/chat/status/{session_id}` | Get session health status |

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sessions` | List all sessions |
| POST | `/api/v1/sessions` | Create new session |
| PUT | `/api/v1/sessions/{session_id}` | Update session metadata |
| DELETE | `/api/v1/sessions/{session_id}` | Delete session |
| GET | `/api/v1/sessions/{session_id}/history` | Get full session message history |

### Copilot

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/copilot` | Send transcript, get AI-suggested reply |
| GET | `/api/v1/copilot/stream/{session_id}` | SSE stream of copilot responses |

### Voice

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voice/twilio` | Twilio webhook handler |
| POST | `/api/v1/voice/twilio/status` | Twilio call status callback |
| GET | `/api/v1/voice/twilio/status/{call_sid}` | Get voice call status |
| POST | `/api/v1/voice/simulate` | Simulate voice call (dev mode) |
| GET | `/api/v1/voice/logs` | Get recent voice call logs |

### Admin / Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/status` | System status with fallback warnings |
| GET | `/api/v1/admin/llm/models` | List configured LLM models |
| GET | `/api/v1/admin/agents` | List configured agents + models |
| GET | `/api/v1/admin/logs` | Get recent server logs |
| GET | `/api/v1/health` | Health check (no auth required) |

### Integrations Vault

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/vault/credentials` | List credential keys (values hidden) |
| POST | `/api/v1/vault/credentials` | Store credential |
| GET | `/api/v1/vault/credentials/{key}` | Retrieve credential |
| DELETE | `/api/v1/vault/credentials/{key}` | Delete credential |

### iPaaS Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/ipaa` | Webhook receiver |
| GET | `/api/v1/webhooks/ipaa/events` | Get recent events |

---

## Telephony & Voice

### Supported Providers

| Provider | Type | Status |
|----------|------|--------|
| Twilio | PSTN (Programmable Voice) | ✅ Production |
| Amazon Connect | CCaaS | ✅ Production |
| Generic SIP / CCaaS | Any SIP trunk | ✅ Production |
| VAPI.ai | AI voice agent overlay | ✅ tested |
| Retell AI | AI voice agent overlay | ✅ tested |
| Simulator | Dev-only (no hardware) | ✅ built-in |

### Call Flow

```
Inbound Call → Twilio Webhook
  → /api/v1/voice/twilio
  → <Gather> input → STT (Deepgram/AssemblyAI)
  → Orchestrator → LLM → TTS (ElevenLabs/PlayHT)
  → <Say> response
    ↺ Loop until hangup
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No* | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key |
| `GEMINI_API_KEY` | No | — | Google Gemini API key |
| `DEFAULT_LLM_MODEL` | No | `gpt-4o-mini` | Default model |
| `TWILIO_ACCOUNT_SID` | No | — | Twilio SID |
| `TWILIO_AUTH_TOKEN` | No | — | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | No | — | Twilio phone number |
| `DEEPGRAM_API_KEY` | No | — | Deepgram STT |
| `ASSEMBLYAI_API_KEY` | No | — | AssemblyAI STT |
| `ELEVENLABS_API_KEY` | No | — | ElevenLabs TTS |
| `PLAYHT_API_KEY` | No | — | PlayHT TTS |
| `JWT_SECRET` | No | — | JWT signing secret |
| `SETTINGS_ADMIN_TOKEN` | No | — | Admin API token |
| `VAULT_ENCRYPTION_KEY` | No | — | AES-256-GCM vault key |

> \* `OPENAI_API_KEY` not strictly required — without it, the platform uses a mock LLM.\
> Full config reference in `config/environment/.env.example`.

---

## Feedback Loop

```
User rates response (👍/👎/CSAT)
  → /api/v1/feedback
  → Feedback Engine
    ├→ Adjusts agent prompt temperature
    ├→ Adjusts RAG retrieval threshold
    ├→ Updates sentiment tracking
    └→ Logs to feedback store
```

---

## Agents Configuration

Agents are defined in `config/agents/`. Example (`config/agents/support.yaml`):

```yaml
name: acme_support
display_name: ACME Support Agent
model: gpt-4o-mini
temperature: 0.7
system_prompt: |
  You are a helpful support agent for ACME Corp.
  Answer questions based on the knowledge base.
  Always cite sources when providing information.
knowledge_base:
  type: markdown
  source: docs/knowledge_base/acme_support.md
rag:
  enabled: true
  chunk_size: 512
  top_k: 3
```

---

## Project Layout

```
nexus/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── routers/
│   │   ├── chat.py                # Chat endpoints
│   │   ├── copilot.py             # Copilot endpoints
│   │   ├── voice.py               # Voice endpoints
│   │   ├── sessions.py            # Session management
│   │   ├── admin.py               # Admin utilities
│   │   ├── vault.py               # Encrypted credentials API
│   │   └── webhooks.py            # iPaaS webhook receiver
│   ├── orchestrator/
│   │   ├── session_manager.py     # Session lifecycle
│   │   ├── prompt_builder.py      # System prompt construction
│   │   ├── agent_router.py        # Model/agent selection
│   │   └── models.py              # Data models, mode enums
│   ├── services/
│   │   ├── llm_service.py         # LLM abstraction layer
│   │   ├── rag_engine.py          # Vector-based RAG
│   │   ├── feedback_engine.py     # CSAT-driven tuning
│   │   ├── vault.py               # AES-256-GCM encryption
│   │   └── ipaa_service.py        # iPaaS webhook dispatch
│   └── llm/
│       ├── providers/
│       │   ├── openai_provider.py # GPT-4o / GPT-4o-mini
│       │   ├── anthropic_provider.py  # Claude 3.5
│       │   └── gemini_provider.py     # Gemini 2.0 Flash
│       └── mock_provider.py       # Mock LLM (dev/tests)
├── static/
│   └── index.html                 # Console UI
├── config/
│   ├── agents/                    # Agent YAML definitions
│   └── environment/
│       └── .env.example           # Environment template
├── docs/
│   ├── overview.md                # This file
│   ├── technical/                 # Architecture, timing
│   ├── assets/                    # Screenshots, demos
│   └── integrations/              # Twilio, CRM, Slack
├── deploy/
│   └── docker/
│       └── docker-compose.yml     # Container deployment
├── tests/                         # 158+ unit + 33 E2E
├── scripts/                       # Dev/CI utilities
└── pyproject.toml                 # Project metadata, deps
```

---

## Dependencies

- **Python** 3.11+
- **FastAPI** — async web framework
- **Pydantic** — data validation
- **SSE-Starlette** — server-sent events for streaming
- **OpenAI / Anthropic / Gemini SDKs** — LLM providers
- **Twilio SDK** — voice telephony
- **Cryptography** — AES-256-GCM vault encryption
- **Pytest / Ruff / Mypy** — testing, linting, types
- **Jinja2** — template rendering (A2F email)
- **httpx** — async HTTP (iPaaS webhooks)

---

## Environment Setup

```bash
cp config/environment/.env.example config/environment/.env
# Edit .env with your API keys
```

---

## Health Check

```bash
curl http://127.0.0.1:8001/api/v1/health
# {"status":"healthy","timestamp":"2025-01-01T00:00:00Z","version":"1.0.0"}
```

---

## Related Documentation

- [Architecture](docs/technical/ARCHITECTURE.md) — system context, data flow, component interaction
- [Integrations](docs/integrations/) — Twilio, CRM, Slack, iPaaS webhook export templates
