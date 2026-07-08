# Nexus — AI Ops Platform

**Omnichannel AI command centre for customer support.**  
Open source. Chat, copilot, and voice — unified.

- **Repository:** [github.com/ShubhamRSY/voice-agents](https://github.com/ShubhamRSY/voice-agents)
- **License:** MIT

---

## What Is Nexus?

Nexus is an open-source, omnichannel AI agent platform built for customer support and contact centres. It replaces three separate tools — live chat, AI copilot, and phone systems — with one AI-powered console. A single orchestrator routes conversations across channels, remembers context, retrieves knowledge, and streams responses in real time via SSE and WebSocket.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Client Channels                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Web      │  │ PSTN/CCaaS   │  │ REST / WebSocket     │   │
│  │ Console  │  │ Twilio · AWS │  │ CRM · Custom Apps    │   │
│  │ Chat/Cop │  │ Connect · SIP│  │ iPaaS (n8n/Zapier)   │   │
│  └────┬─────┘  └──────┬───────┘  └───────────┬──────────┘   │
└───────┼───────────────┼───────────────────────┼──────────────┘
        │               │                       │
┌───────▼───────────────▼───────────────────────▼──────────────┐
│                     API Gateway (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Middleware: CORS → Tenant Isolation → Rate Limit    │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │  Domain Routers (under /api/v1):                     │    │
│  │  Auth · Chat (+ SSE/WS stream) · KB · Telephony     │    │
│  │  Integrations · Ops (health/metrics/feedback/events) │    │
│  └──────────────────────┬───────────────────────────────┘    │
└─────────────────────────┼────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   Agent Orchestrator                          │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐    │
│  │ Channel     │  │ Prompt      │  │ Tool Execution    │    │
│  │ Router      │  │ Builder     │  │ Engine            │    │
│  │             │  │ (per-mode)  │  │ (RAG, CRM, etc.)  │    │
│  └──────┬──────┘  └──────┬──────┘  └────────┬──────────┘    │
└─────────┼────────────────┼──────────────────┼────────────────┘
          │                │                  │
┌─────────▼────────────────▼──────────────────▼────────────────┐
│                       Core Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ Chat     │ │ Voice    │ │ Feedback │ │ Integrations   │  │
│  │ Handler  │ │ Handler  │ │ Engine   │ │ Vault          │  │
│  │          │ │ (Twilio, │ │ (CSAT    │ │ (Encrypted     │  │
│  │          │ │ Connect, │ │  auto-   │ │  API keys)     │  │
│  │          │ │  SIP)    │ │  adjust) │ │                │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ RAG      │ │ LLM      │ │ Database │ │ Audio/STT/TTS  │  │
│  │ Pipeline │ │ Client   │ │ (SQLite  │ │ Engine         │  │
│  │ (vector  │ │ (OpenAI, │ │  + vec-  │ │                │  │
│  │  search) │ │ Claude,  │ │  tor db) │ │                │  │
│  │          │ │ Gemini)  │ │          │ │                │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Components

### API Gateway (FastAPI)
Single Python application serving the web console, REST API, and WebSocket connections. Middleware stack handles CORS, tenant isolation, rate limiting, and authentication.

- **Source:** [`src/main.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/main.py)
- **Domain routers:**
  - `auth_routes` — `/api/v1/auth/*` — register, login, JWT
  - `chat_routes` — `/api/v1/chat*` — chat, copilot, CSAT, SSE streaming
  - `kb_routes` — `/api/v1/kb/*` — knowledge base CRUD
  - `telephony_routes` — `/api/v1/voice/*` — Twilio, voice simulation
  - `integration_routes` — `/api/v1/integrations/*` — vault, webhooks
  - `ops_routes` — `/api/v1/*` — health, metrics, feedback, agents, events

### Agent Orchestrator
Routes inbound requests to the correct channel handler, builds channel-specific prompts, manages conversation state, and executes tool calls (RAG retrieval, CRM lookups, etc.) before returning the LLM response. Supports both `invoke()` (full response) and `invoke_stream()` (token-by-token async generator).

- **Source:** [`src/workflows/orchestrator.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/workflows/orchestrator.py)

### Channel Handlers
Each channel has a dedicated handler that normalises input/output for the orchestrator:

| Channel | Handler | Protocol |
|---------|---------|----------|
| Chat (Web UI) | `ChatHandler` | HTTP + SSE + WebSocket |
| Copilot | `CopilotHandler` | HTTP (transcript in → reply out) |
| Voice (Twilio) | `TwilioHandler` | TwiML + Media Streams |
| Voice (Amazon Connect) | `AmazonConnectHandler` | Lambda-style JSON webhooks |
| Generic CCaaS | `CcaasVoiceHandler` (abstract base) | Extensible for any SIP/CCaaS |

- **Twilio:** [`src/telephony/twilio_handler.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/twilio_handler.py)
- **Amazon Connect:** [`src/telephony/amazon_connect_handler.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/amazon_connect_handler.py)
- **CCaaS Base:** [`src/telephony/ccaas_base.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/ccaas_base.py)

### LLM Client
Abstract client layer supporting OpenAI GPT-4o, Anthropic Claude 3.5, and Google Gemini 2.0. Configurable per conversation — operators can switch models without restarting.

- **Source:** [`src/llm/factory.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/llm/factory.py)

### RAG Pipeline
Retrieval-augmented generation pipeline that searches a vector database (ChromaDB/FAISS) for relevant knowledge chunks before every LLM call. Responses include source citations and grounding metrics.

- **Source:** [`src/rag/`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/rag/)

### Feedback Engine
Post-interaction CSAT surveys feed into an auto-adjustment engine. Scores trigger automatic tuning of agent personality, response length, escalation thresholds, and tone — no manual intervention needed.

- **Source:** [`src/feedback/engine.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/feedback/engine.py)
- **API Endpoints:** `/api/v1/feedback/` (report, config, suggestions, auto-adjust)

### Integrations Vault
Encrypted store for all third-party API keys (AES-256-GCM). Keys are never logged, never exposed in responses, and never hardcoded. Supports OpenAI, Anthropic, Gemini, Twilio, Salesforce, Zendesk, ServiceNow, Slack.

- **Source:** [`src/integrations/secrets_vault.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/integrations/secrets_vault.py)

### Database
SQLite database with schema managed via `init_db()`. Tables cover tenants, users, sessions, messages, tool calls, CSAT feedback, and audit logs.

- **Source:** [`src/database.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/database.py)

---

## Data Flow

```
User Message (any channel)
        │
        ▼
  API Gateway (FastAPI)
        │
        ├──► Auth & Tenant Middleware
        ├──► Rate Limiting
        │
        ▼
  Channel Router (normalises input)
        │
        ▼
  Agent Orchestrator
        │
        ├──► Builds prompt (channel-specific)
        ├──► Executes tools (RAG, CRM, etc.)
        ├──► Calls LLM (OpenAI / Claude / Gemini)
        │
        ▼
  Response Streams Back
        ├──► Chat: SSE/WebSocket to console (token by token)
        ├──► Copilot: Full suggested reply
        └──► Voice: TTS audio via Twilio Media Streams
        │
        ▼
  Logging & Feedback
        ├──► Session + messages stored in DB
        └──► CSAT survey → Feedback Engine → auto-adjust
```

---

## Channels Detail

### Chat
Full-featured web chat interface with real-time streaming via Server-Sent Events (`GET /api/v1/chat/sse`) and WebSocket (`ws://.../chat/stream`). Both use the `orchestrator.invoke_stream()` async generator which yields tokens directly from the LLM's `astream_events()`. Supports multi-line input, conversation history, and tool call visibility.

### Copilot
Agent-assist mode. Support agents paste a ticket transcript, Nexus analyses the conversation and generates a suggested reply. The agent reviews and edits before sending — human-in-the-loop.

### Voice (Twilio)
Inbound and outbound PSTN calls via Twilio. Live speech-to-text transcription streams to the console. AI responses are spoken back using text-to-speech (OpenAI TTS or ElevenLabs). Call recordings, logs, and transcripts are saved automatically.

- **Twilio Setup:** [`docs/integrations/twilio-setup.md`](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/twilio-setup.md)

### Voice (Amazon Connect)
Lambda-style webhook handler for AWS Connect contact flows. Accepts JSON payloads with contact flow attributes, processes them through the orchestrator, and returns JSON responses for branch conditions.

### Voice (Generic CCaaS)
Abstract `CcaasVoiceHandler` base class in [`src/telephony/ccaas_base.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/ccaas_base.py). Implement `handle_inbound`, `handle_process`, and `handle_status_callback` to add any SIP or CCaaS provider.

---

## Integrations

| Category | Providers | Documentation |
|----------|-----------|---------------|
| **LLMs** | OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0 | [LLM Config](https://github.com/ShubhamRSY/voice-agents/blob/main/src/llm/factory.py) |
| **Telephony** | Twilio (PSTN + WhatsApp), Amazon Connect, generic SIP/CCaaS | [Twilio Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/twilio-setup.md) |
| **CRMs** | Salesforce, Zendesk, ServiceNow | [CRM Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/crm-setup.md) |
| **Notifications** | Slack | [Slack Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/slack-setup.md) |
| **iPaaS** | n8n, Zapier | [n8n Workflow](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/templates/n8n-workflow.json) · [Zapier Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/templates/zapier-setup.md) |

All credentials stored in the encrypted Integrations Vault — never in config files or environment variables.

---

## API Overview

Selected REST API endpoints (full reference at `/docs` when running):

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | Server + STT/TTS health check |
| `POST` | `/api/v1/auth/register` | Register tenant + admin user |
| `POST` | `/api/v1/auth/login` | Login, receive JWT |
| `POST` | `/api/v1/chat` | Send chat message, get response |
| `GET` | `/api/v1/chat/sse` | SSE streaming chat (token-by-token) |
| `WS` | `/api/v1/chat/stream` | WebSocket streaming chat |
| `POST` | `/api/v1/copilot` | Analyse transcript, suggest reply |
| `POST` | `/api/v1/voice/twilio` | Twilio webhook handler |
| `POST` | `/api/v1/voice/connect` | Amazon Connect webhook handler |
| `GET` | `/api/v1/sessions/stats` | Active session count |
| `GET` | `/api/v1/sessions/{id}/history` | Get session messages |
| `POST` | `/api/v1/csat` | Submit CSAT score |
| `GET` | `/api/v1/feedback/{agent_id}/report` | Agent feedback report |
| `GET` | `/api/v1/metrics` | Prometheus metrics |
| `GET` | `/api/v1/agents` | List configured agents |
| `GET` | `/api/v1/llm/config` | LLM configuration |

---

## Deployment

| Method | Command / Details |
|--------|------------------|
| **Docker** | `docker compose -f deploy/docker/docker-compose.yml up` — single container, all dependencies included |
| **Bare metal** | `uvicorn src.main:app --host 0.0.0.0 --port 8001` behind nginx/Caddy |
| **Production (multi-worker)** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8001 --timeout 120 --graceful-timeout 30` |
| **CI/CD** | GitHub Actions — lint, test, e2e, docker build |

### Dockerfile Optimizations

The production Dockerfile (`deploy/docker/Dockerfile`) uses a multi-stage build:

- **Builder stage:** Python 3.12-slim, minimal build deps (`gcc` + `libffi-dev`), `--no-build-isolation` pip installs
- **Runtime stage:** Python 3.12-slim, only `site-packages` + `src` + `config` + `static` + `data` copied (no tests/docs/scripts)
- Non-root user (`appuser`), `wget`-based healthcheck, gunicorn with 4 uvicorn workers

### CI Pipeline (`.github/workflows/ci.yml`)

| Job | What It Does |
|-----|-------------|
| `lint` | Ruff linting + mypy type checking (strict, no `|| true`) + pip-audit vulnerability scan |
| `test` (3.11, 3.12) | Pytest with `--timeout=60`, 95+ unit tests |
| `e2e` | Live server start → 33 Playwright E2E tests |
| `docker` | Builds Docker image, smoke-test |

---

## Security

- **Credentials:** AES-256-GCM encrypted at rest in the Integrations Vault. Never logged, never exposed in API responses.
- **Authentication:** JWT-based auth with configurable expiry. Tenant isolation at middleware level.
- **Input validation:** Pydantic models on all API endpoints with descriptions and examples. SQL injection prevented via parameterised queries.
- **CORS:** Strict origin whitelist. No wildcard in production.
- **Dependencies:** `pip-audit --strict` runs in CI to scan for known vulnerabilities.

---

## Quick Start

```bash
git clone https://github.com/ShubhamRSY/voice-agents.git
cd voice-agents
pip install -e ".[dev]"
cp config/environment/.env.example config/environment/.env   # add your API keys
uvicorn src.main:app --reload --port 8001
```

Open [http://localhost:8001](http://localhost:8001) in a browser.

---

## Testing

```bash
# Unit tests
pytest tests/ --timeout=60 -v

# Lint + type check + security audit
ruff check src/ scripts/
mypy src/ --ignore-missing-imports
pip install pip-audit && pip-audit --strict
```

---

## Project Structure

```
├── config/
│   ├── agents.yaml           # Agent definitions & LLM config
│   └── environment/
│       ├── .env              # Local overrides (gitignored)
│       └── .env.example      # Environment variable template
├── deploy/
│   └── docker/
│       ├── docker-compose.yml # Container orchestration
│       └── Dockerfile         # Production multi-stage build
├── docs/
│   ├── assets/               # Demo videos & media
│   ├── technical/            # Architecture docs (this file)
│   └── integrations/         # Setup guides + templates
├── scripts/
│   ├── demo.py               # Narrated product demo
│   ├── ingest_kb.py          # Knowledge base ingestion
│   └── generate_ppt.py       # Presentation generator
├── src/                      # Application source
│   ├── main.py               # FastAPI app entry point
│   ├── api/                  # Domain routers (6 modules)
│   ├── workflows/            # Agent orchestrator
│   ├── telephony/            # Voice handlers
│   ├── feedback/             # Feedback loop engine
│   ├── integrations/         # Vault, webhooks, CRMs
│   ├── llm/                  # LLM client (OpenAI, Claude, Gemini)
│   ├── rag/                  # RAG pipeline + vector search
│   ├── database.py           # SQLite + migrations
│   ├── auth.py               # JWT authentication
│   └── config.py             # Settings (pydantic-settings)
├── static/
│   └── index.html            # Web console UI
├── tests/
│   ├── test_*.py             # 95+ unit tests
│   ├── e2e/                  # E2E journey tests
│   └── test_comprehensive_e2e.py  # 33 E2E tests
└── .github/workflows/ci.yml  # GitHub Actions CI
```

---

## Changelog (Recent)

| Date | Change |
|------|--------|
| Jun 2025 | **Routes refactored** — monolithic `routes.py` split into 6 domain modules |
| Jun 2025 | **SSE streaming** — `GET /api/v1/chat/sse` for token-by-token streaming |
| Jun 2025 | **Dockerfile optimized** — multi-stage, Python 3.12, gunicorn, wget healthcheck |
| Jun 2025 | **CI hardened** — pip-audit vulnerability scan, strict mypy |
| Jun 2025 | **API docs enhanced** — descriptions + examples on all Pydantic models |
| Jun 2025 | **Config cleanup** — unused path constants removed |
| Jun 2025 | **Database fix** — `isolation_level=None` for proper autocommit |
| Jun 2025 | **Test expansion** — 6 new streaming tests, 95+ unit tests passing |

---

*Nexus AI Ops — one console for every conversation.*
