<div align="center">

# Nexus

**Open-source omnichannel AI agent platform for contact centers.**  
One orchestrator routing chat, copilot, and voice conversations — with RAG, multi-LLM support, SSE streaming, and WebSocket streaming.

[![CI](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-95%2B%20unit%20passing-brightgreen.svg)](tests/)

</div>

---

## Table of Contents

- [What Is Nexus?](#what-is-nexus)
- [Recent Changes](#recent-changes)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
- [API Overview](#api-overview)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## What Is Nexus?

Customer support teams lose context switching between channels — chat, phone, email, and internal tools each live in separate silos. Nexus solves this with a single AI-powered orchestrator that handles every conversation from one runtime, with one knowledge base, and one feedback loop to improve responses over time.

**Three channels, one engine:**

| Channel | Purpose |
|---------|---------|
| **Chat** | Live AI conversation with SSE streaming, WebSocket streaming, RAG citations, full session history |
| **Copilot** | Agent-assist — paste a transcript, get an AI-suggested reply |
| **Voice** | PSTN calls via Twilio, Amazon Connect, or any SIP/CCaaS. Live STT, AI TTS. |

> **No API key required.** Without `OPENAI_API_KEY`, Nexus falls back to a mock LLM — the console, voice simulator, smoke tests, and all 95+ unit tests work immediately.

---

## Recent Changes

| Change | Description |
|--------|-------------|
| **Routes refactored** | Monolithic `routes.py` split into domain modules: `auth_routes`, `chat_routes`, `kb_routes`, `telephony_routes`, `integration_routes`, `ops_routes` |
| **SSE streaming endpoint** | New `GET /api/v1/chat/sse` for token-by-token streaming via Server-Sent Events |
| **Dockerfile optimized** | Multi-stage build, Python 3.12-slim, gunicorn with uvicorn workers, `wget` healthcheck, non-root user |
| **CI hardened** | Added `pip-audit --strict` dependency vulnerability scan; strict mypy (no `|| true`) |
| **Enhanced API docs** | All Pydantic models now have `description` and `examples` — visible in `/docs` |
| **Config cleanup** | Removed unused path constants from `src/config.py` |
| **Database fix** | `isolation_level=None` ensures proper autocommit across reconnects |
| **Test expansion** | 6 new streaming tests (SSE + WebSocket); 95+ unit tests passing |

---

## Prerequisites

- **Python 3.11+**
- **pip** (bundled with Python)
- **git**
- *(Optional)* An [OpenAI](https://platform.openai.com/api-keys), [Anthropic](https://console.anthropic.com/), or [Google Gemini](https://ai.google.dev/) API key for production LLM access
- *(Optional)* [Docker](https://www.docker.com/) for containerized deployment

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ShubhamRSY/voice-agents.git
cd voice-agents

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Copy the environment template (no edits needed to start)
cp config/environment/.env.example config/environment/.env
```

---

## Quick Start

```bash
# Start the server
uvicorn src.main:app --reload --port 8001
```

Open **[http://127.0.0.1:8001](http://127.0.0.1:8001)** — the Nexus console loads with a welcome screen, session sidebar, and channel selector.

**Smoke test the API:**

```bash
# Non-streaming chat
curl -s -X POST http://127.0.0.1:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I reset my password?","session_id":"demo-1"}' | jq

# SSE streaming chat
curl -s http://127.0.0.1:8001/api/v1/chat/sse?message=Hello

# WebSocket streaming (via wscat)
wscat -c ws://127.0.0.1:8001/api/v1/chat/stream
```

**Health check:**

```bash
curl http://127.0.0.1:8001/api/v1/health
```

---

## Architecture

```
User Message → REST API → Orchestrator
  ├→ Session Manager (create/load session)
  ├→ RAG Engine (retrieve context + citations)
  ├→ Prompt Builder (system prompt + history + context)
  ├→ LLM Provider (streaming SSE/WebSocket response)
  └→ Response → Console
```

Nexus follows a layered design: domain routers (`auth_routes`, `chat_routes`, `kb_routes`, `telephony_routes`, `integration_routes`, `ops_routes`) handle channel-specific logic, the orchestrator manages session state and prompt construction, services provide RAG and feedback, and a provider layer abstracts over OpenAI, Anthropic, and Gemini models.

Full architecture and data flow diagrams → [docs/overview.md](docs/overview.md#architecture).

---

## Features

- **Omnichannel** — unified console for chat, copilot, and voice with per-mode message filtering and sync toggle
- **Multi-LLM** — OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0 — switch per agent
- **Live streaming** — SSE (`GET /api/v1/chat/sse`) and WebSocket (`ws://.../chat/stream`) deliver tokens word-by-word
- **RAG citations** — vector-based retrieval augments every response with source-grounded knowledge
- **Voice (PSTN)** — Twilio, Amazon Connect, generic SIP/CCaaS with STT/TTS pipeline
- **Feedback engine** — CSAT ratings dynamically tune agent temperature and RAG thresholds
- **Encrypted vault** — AES-256-GCM for API keys and integration credentials at rest
- **Session management** — history sidebar, rename, new/clear session
- **iPaaS webhooks** — lifecycle events (session.created, message.completed, feedback.submitted) for n8n/Zapier
- **Dark mode UI** — polished frontend with animations, typing indicator, streaming cursor

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new tenant + admin user |
| POST | `/api/v1/auth/login` | Login, receive JWT |
| GET | `/api/v1/auth/me` | Current user info |
| POST | `/api/v1/chat` | Send message, get AI response |
| GET | `/api/v1/chat/sse` | SSE streaming chat (token-by-token) |
| WS | `/api/v1/chat/stream` | WebSocket streaming chat |
| POST | `/api/v1/copilot` | Agent-assist: transcript → suggested reply |
| DELETE | `/api/v1/chat/{session_id}` | End a session |
| GET | `/api/v1/sessions/stats` | Active session count |
| GET | `/api/v1/sessions/{id}/history` | Session message history |
| POST | `/api/v1/csat` | Submit CSAT rating |
| GET | `/api/v1/csat/stats` | CSAT statistics |
| GET | `/api/v1/agents` | List configured agents |
| GET | `/api/v1/llm/config` | LLM configuration overview |
| GET | `/api/v1/health` | Health check (no auth) |
| GET | `/api/v1/metrics` | Prometheus metrics |
| GET | `/api/v1/feedback/{agent_id}/report` | Agent feedback report |
| POST | `/api/v1/demo/reset` | Reset demo data |
| POST | `/api/v1/events` | Receive external events |

Full reference at `/docs` when the server is running.

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

## Deployment

| Method | Command |
|--------|---------|
| **Docker** | `docker compose -f deploy/docker/docker-compose.yml up` |
| **Bare metal** | `uvicorn src.main:app --host 0.0.0.0 --port 8001` |
| **Production (multi-worker)** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8001 --timeout 120 --graceful-timeout 30` |
| **CI/CD** | GitHub Actions — lint (ruff + mypy + pip-audit), test, e2e, docker build |

---

## Contributing

1. Fork the repo and create a branch from `main`
2. Run tests locally with `pytest tests/`
3. Lint with `ruff check src/ scripts/`
4. Run type check with `mypy src/`
5. Submit a pull request

All contributions — features, bug fixes, docs, tests — are welcome.

---

## License

[MIT](LICENSE) © [Shubham RSY](https://github.com/ShubhamRSY)
