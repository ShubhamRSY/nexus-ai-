# Nexus Overview

> **Nexus** is an open-source, enterprise-grade omnichannel AI agent platform that unifies chat, copilot, and voice into a single orchestration runtime.

---

## Architecture

Nexus follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                  Console (Web UI)                │
│    HTML/CSS/JS  ←  SSE/WS Streaming  ←  REST   │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              FastAPI Application                 │
│    ┌────────┐ ┌──────────┐ ┌───────────────┐    │
│    │ Auth   │ │ Chat     │ │ Voice         │    │
│    │ Router │ │ Router   │ │ Router        │    │
│    └───┬────┘ └────┬─────┘ └──────┬────────┘    │
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
  ├→ LLM (streaming SSE/WebSocket response)
  └→ Response → Console
```

### Core Components

- **Auth Router** — `/api/v1/auth/*` — register, login, JWT-based authentication
- **Chat Router** — `/api/v1/chat*` — conversational AI with SSE and WebSocket streaming
- **Copilot Router** — `/api/v1/copilot` — agent-assist for live agents
- **Voice Router** — `/api/v1/voice/*` — PSTN telephony integration with Twilio/AWS Connect
- **KB Router** — `/api/v1/kb/*` — knowledge base management
- **Integration Router** — `/api/v1/integrations/*` — vault, webhooks, CRM
- **Ops Router** — `/api/v1/*` — health, metrics, feedback, analytics, demo, events
- **Orchestrator** — session manager + prompt builder + agent router
- **RAG Engine** — vector-based retrieval augmented generation with source citations
- **Feedback Engine** — CSAT-driven auto-tuning of agent parameters
- **Vault** — AES-256-GCM encrypted credentials storage for integrations
- **iPaaS Webhooks** — lifecycle events (session.created, message.completed, feedback.submitted)

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register tenant + admin user |
| POST | `/api/v1/auth/login` | Login, receive JWT |
| GET | `/api/v1/auth/me` | Current user info |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message, get AI response |
| GET | `/api/v1/chat/sse` | SSE streaming (token-by-token) |
| WS | `/api/v1/chat/stream` | WebSocket streaming |
| DELETE | `/api/v1/chat/{session_id}` | End session |

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sessions/stats` | Active session count |
| GET | `/api/v1/sessions/{session_id}/history` | Session message history |

### Copilot

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/copilot` | Send transcript, get AI-suggested reply |

### Voice

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voice/twilio` | Twilio webhook handler |
| POST | `/api/v1/voice/twilio/status` | Twilio call status callback |
| GET | `/api/v1/voice/twilio/status/{call_sid}` | Get voice call status |
| POST | `/api/v1/voice/simulate` | Simulate voice call (dev mode) |
| GET | `/api/v1/voice/logs` | Get recent voice call logs |

### CSAT / Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/csat` | Submit CSAT rating |
| GET | `/api/v1/csat/stats` | CSAT statistics |
| GET | `/api/v1/feedback/{agent_id}/report` | Agent feedback report |
| GET | `/api/v1/feedback/{agent_id}/config` | Feedback config |
| GET | `/api/v1/feedback/{agent_id}/suggestions` | Improvement suggestions |

### Admin / Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check (no auth required) |
| GET | `/api/v1/metrics` | Prometheus metrics |
| GET | `/api/v1/observability/health` | Observability dashboard |
| GET | `/api/v1/agents` | List configured agents |
| GET | `/api/v1/llm/config` | LLM configuration |
| POST | `/api/v1/demo/reset` | Reset demo data |
| POST | `/api/v1/events` | Receive external events |
| GET | `/api/v1/tasks/{task_id}` | Task status |

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
| `DEFAULT_LLM_PROVIDER` | No | `openai` | Default LLM provider |
| `DEFAULT_LLM_MODEL` | No | `gpt-4o-mini` | Default model |
| `APP_HOST` | No | `0.0.0.0` | Bind address |
| `APP_PORT` | No | `8001` | HTTP port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `TWILIO_ACCOUNT_SID` | No | — | Twilio SID |
| `TWILIO_AUTH_TOKEN` | No | — | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | No | — | Twilio phone number |
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

Agents are defined in `config/agents.yaml`. Example:

```yaml
agents:
  chat_support:
    name: "Chat Support Agent"
    channel: chat
    llm_provider: openai
    llm_model: gpt-4o-mini
    temperature: 0.4
    max_tokens: 1024
    tools:
      - lookup_customer
      - search_knowledge_base
      - create_ticket

llm_defaults:
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0

guardrails:
  enabled: true
  block_prompt_injection: true

rag:
  chunk_size: 512
  top_k: 5
  score_threshold: 0.7
```

---

## Project Layout

```
nexus/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── api/
│   │   ├── auth_routes.py         # Authentication endpoints
│   │   ├── chat_routes.py         # Chat, copilot, CSAT, SSE streaming
│   │   ├── kb_routes.py           # Knowledge base CRUD
│   │   ├── telephony_routes.py    # Voice/Twilio endpoints
│   │   ├── integration_routes.py  # Vault, webhooks
│   │   ├── ops_routes.py          # Health, metrics, feedback, demo, events
│   │   ├── deps.py                # Shared models, singletons, auth deps
│   │   └── session_manager.py     # TTL-backed session store
│   ├── workflows/
│   │   └── orchestrator.py        # Agent orchestrator (session, prompt, LLM)
│   ├── llm/
│   │   ├── factory.py             # LLM provider factory
│   │   ├── params.py              # LLM parameter resolution
│   │   ├── guardrails.py          # Input/output guardrails
│   │   └── hallucination.py       # Hallucination detection
│   ├── rag/
│   │   ├── vector_store.py        # ChromaDB vector store
│   │   ├── retriever.py           # RAG context formatter
│   │   ├── ingestion.py           # Document ingestion
│   │   └── keyword_search.py      # FAQ keyword fallback
│   ├── feedback/
│   │   └── engine.py              # Feedback loop + tuning
│   ├── integrations/
│   │   ├── secrets_vault.py       # AES-256-GCM encrypted vault
│   │   ├── webhooks.py            # iPaaS webhook dispatch
│   │   ├── slack.py, crm.py, ...  # Third-party integrations
│   ├── telephony/                  # Voice handlers
│   ├── auth.py                    # JWT auth, password hashing
│   ├── database.py                # SQLite + migrations
│   ├── observability.py           # Metrics, Sentry, OpenTelemetry
│   ├── logging_config.py          # Structured logging
│   ├── middleware.py              # CORS, tenant, rate limit
│   ├── tasks.py                   # Background task queue
│   └── analytics.py               # Analytics dashboard
├── static/
│   └── index.html                 # Console UI
├── config/
│   ├── agents.yaml                # Agent definitions
│   └── environment/
│       ├── .env                   # Local overrides (gitignored)
│       └── .env.example           # Environment template
├── deploy/
│   └── docker/
│       ├── docker-compose.yml     # Container deployment
│       └── Dockerfile             # Production multi-stage build
├── docs/
│   ├── overview.md                # This file
│   ├── technical/                 # Architecture docs
│   └── integrations/              # Setup guides
├── tests/                         # 95+ unit tests
├── scripts/                       # Dev/CI utilities
└── pyproject.toml                 # Project metadata, deps
```

---

## Dependencies

- **Python** 3.11+
- **FastAPI** — async web framework
- **Pydantic** — data validation (descriptions + examples on all models)
- **Uvicorn / Gunicorn** — ASGI / production WSGI server
- **LangChain / LangGraph** — LLM abstraction, agent workflows
- **ChromaDB** — vector store for RAG
- **OpenAI / Anthropic / Gemini SDKs** — LLM providers
- **Twilio SDK** — voice telephony
- **Cryptography** — AES-256-GCM vault encryption
- **Structlog** — structured logging
- **Pytest / Ruff / Mypy / pip-audit** — testing, linting, types, security

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
# {"status":"healthy","service":"enterprise-voice-agents","stt_available":true,...}
```

---

## Related Documentation

- [Architecture](docs/technical/ARCHITECTURE.md) — system context, data flow, component interaction
- [Integrations](docs/integrations/) — Twilio, CRM, Slack, iPaaS webhook export templates
