# Nexus — AI Ops Platform

**Omnichannel AI command centre for customer support.**  
Open source. Chat, copilot, and voice — unified.

- **Repository:** [github.com/ShubhamRSY/voice-agents](https://github.com/ShubhamRSY/voice-agents)
- **License:** MIT

---

## What Is Nexus?

Nexus is an open-source, omnichannel AI agent platform built for customer support and contact centres. It replaces three separate tools — live chat, AI copilot, and phone systems — with one AI-powered console. A single orchestrator routes conversations across channels, remembers context, retrieves knowledge, and streams responses in real time.

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
│  │  Routes: Chat · Voice · Copilot · RAG · Knowledge    │    │
│  │          Base · Analytics · Evaluation · Feedback     │    │
│  │          Integrations · Auth · Health                 │    │
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
- **Routes:** [`src/api/routes.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/api/routes.py)

### Agent Orchestrator
Routes inbound requests to the correct channel handler, builds channel-specific prompts, manages conversation state, and executes tool calls (RAG retrieval, CRM lookups, etc.) before returning the LLM response.

- **Source:** [`src/agents/orchestrator.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/agents/orchestrator.py)

### Channel Handlers
Each channel has a dedicated handler that normalises input/output for the orchestrator:

| Channel | Handler | Protocol |
|---|---|---|
| Chat (Web UI) | `ChatHandler` | HTTP + SSE |
| Copilot | `CopilotHandler` | HTTP (transcript in → reply out) |
| Voice (Twilio) | `TwilioHandler` | TwiML + Media Streams |
| Voice (Amazon Connect) | `AmazonConnectHandler` | Lambda-style JSON webhooks |
| Generic CCaaS | `CcaasVoiceHandler` (abstract base) | Extensible for any SIP/CCaaS |

- **Twilio:** [`src/telephony/twilio_handler.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/twilio_handler.py)
- **Amazon Connect:** [`src/telephony/amazon_connect_handler.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/amazon_connect_handler.py)
- **CCaaS Base:** [`src/telephony/ccaas_base.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/telephony/ccaas_base.py)

### LLM Client
Abstract client layer supporting OpenAI GPT-4o, Anthropic Claude 3.5, and Google Gemini 2.0. Configurable per conversation — operators can switch models without restarting.

- **Source:** [`src/llm/client.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/llm/client.py)

### RAG Pipeline
Retrieval-augmented generation pipeline that searches a vector database (FAISS/chroma) for relevant knowledge chunks before every LLM call. Responses include source citations and grounding metrics.

- **Source:** [`src/rag/`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/rag/)

### Feedback Engine
Post-interaction CSAT surveys feed into an auto-adjustment engine. Scores trigger automatic tuning of agent personality, response length, escalation thresholds, and tone — no manual intervention needed.

- **Source:** [`src/feedback/engine.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/feedback/engine.py)
- **API Endpoints:** `/api/v1/feedback/` (report, analyze, snapshot, config CRUD, suggestions, auto-adjust)

### Integrations Vault
Encrypted store for all third-party API keys (AES-256-GCM). Keys are never logged, never exposed in responses, and never hardcoded. Supports OpenAI, Anthropic, Gemini, Twilio, Salesforce, Zendesk, ServiceNow, Slack.

- **Source:** [`src/integrations/vault.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/integrations/vault.py)

### Database
SQLite database with schema migrations managed via Alembic-style versioning. Tables cover sessions, messages, tool calls, feedback loop config, performance trends, and encrypted credentials.

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
  Channel Handler (normalises input)
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
        ├──► Chat: SSE to web console (token by token)
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
Full-featured web chat interface with real-time streaming via Server-Sent Events. Supports multi-line input, conversation history, and tool call visibility.

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
|---|---|---|
| **LLMs** | OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0 | [LLM Config](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/configuration.md) |
| **Telephony** | Twilio (PSTN + WhatsApp), Amazon Connect, generic SIP/CCaaS | [Twilio Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/twilio-setup.md) |
| **CRMs** | Salesforce, Zendesk, ServiceNow | [CRM Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/crm-setup.md) |
| **Notifications** | Slack | [Slack Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/slack-setup.md) |
| **iPaaS** | n8n, Zapier | [n8n Workflow](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/templates/n8n-workflow.json) · [Zapier Setup](https://github.com/ShubhamRSY/voice-agents/blob/main/docs/integrations/templates/zapier-setup.md) |

All credentials stored in the encrypted Integrations Vault — never in config files or environment variables.

---

## API Overview

Selected REST API endpoints (full reference in [`src/api/routes.py`](https://github.com/ShubhamRSY/voice-agents/blob/main/src/api/routes.py)):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Server + STT/TTS health check |
| `POST` | `/api/v1/chat` | Send chat message, stream response |
| `POST` | `/api/v1/copilot` | Analyse transcript, suggest reply |
| `POST` | `/api/v1/voice/twilio` | Twilio webhook handler |
| `POST` | `/api/v1/voice/connect` | Amazon Connect webhook handler |
| `GET` | `/api/v1/sessions` | List conversation sessions |
| `GET` | `/api/v1/sessions/{id}/messages` | Get session messages |
| `POST` | `/api/v1/feedback/report` | Submit CSAT score |
| `GET` | `/api/v1/feedback/trends` | Get performance trends |
| `POST` | `/api/v1/feedback/auto-adjust` | Trigger automatic tuning |
| `GET` | `/api/v1/integrations` | List integrations / credentials |
| `POST` | `/api/v1/integrations/vault` | Store encrypted credential |

---

## Deployment

| Method | Command / Details |
|---|---|
| **Docker** | `docker compose -f deploy/docker/docker-compose.yml up` — single container, all dependencies included |
| **Bare metal** | `uvicorn src.main:app --host 0.0.0.0 --port 8001` behind nginx/Caddy |
| **CI/CD** | GitHub Actions — lint, 158+ unit tests, 33 E2E tests |

### CI Pipeline (`.github/workflows/ci.yml`)

| Job | What It Does |
|---|---|
| `lint` | Ruff linting + mypy type checking |
| `test` (3.11, 3.12) | Pytest with `--timeout=60`, 158+ unit tests |
| `e2e` | Live server start → 33 Playwright E2E tests |
| `docker` | Builds Docker image, smoke-test |

---

## Security

- **Credentials:** AES-256-GCM encrypted at rest in the Integrations Vault. Never logged, never exposed in API responses.
- **Authentication:** JWT-based auth with configurable expiry. Tenant isolation at middleware level.
- **Input validation:** Pydantic models on all API endpoints. SQL injection prevented via parameterised queries.
- **CORS:** Strict origin whitelist. No wildcard in production.

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

# E2E tests (requires running server on port 8001)
pytest tests/test_comprehensive_e2e.py --timeout=120 -v

# Lint + type check
ruff check src/ scripts/
mypy src/ --ignore-missing-imports
```

---

## Project Structure

```
├── config/
│   ├── agents.yaml           # Agent definitions & LLM config
│   └── environment/
│       └── .env.example      # Environment variable template
├── deploy/
│   └── docker/
│       ├── docker-compose.yml # Container orchestration
│       ├── Dockerfile         # Production image
│       └── .dockerignore
├── docs/
│   ├── assets/               # Demo videos & media
│   │   └── nexus-demo.webm
│   ├── technical/            # Architecture docs (this file)
│   ├── integrations/         # Setup guides + templates
│   └── configuration.md
├── scripts/
│   ├── demo.py               # Narrated product demo
│   └── ci.sh                 # Local CI script
├── src/                      # Application source
│   ├── main.py               # FastAPI app entry point
│   ├── api/routes.py         # All REST API endpoints
│   ├── agents/               # Agent orchestrator + prompt builders
│   ├── telephony/            # Voice handlers (Twilio, Connect, CCaaS)
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
│   ├── test_*.py             # 158+ unit tests
│   ├── e2e/                  # E2E journey tests
│   └── test_comprehensive_e2e.py  # 33 E2E tests
└── .github/workflows/ci.yml  # GitHub Actions CI
```

---

*Nexus AI Ops — one console for every conversation.*
