<div align="center">

# Nexus

**Open-source omnichannel AI agent platform for contact centers.**  
One orchestrator routing chat, copilot, and voice conversations — with RAG, multi-LLM support, and real-time streaming.

[![CI](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-158%2B%20unit%20%7C%2033%20E2E%20passing-brightgreen.svg)](tests/)

</div>

---

## Table of Contents

- [What Is Nexus?](#what-is-nexus)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
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
| **Chat** | Live AI conversation with SSE streaming, RAG citations, full session history |
| **Copilot** | Agent-assist — paste a transcript, get an AI-suggested reply |
| **Voice** | PSTN calls via Twilio, Amazon Connect, or any SIP/CCaaS. Live STT, AI TTS. |

> **No API key required.** Without `OPENAI_API_KEY`, Nexus falls back to a mock LLM — the console, voice simulator, smoke tests, and all 158+ unit tests work immediately.

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
curl -s -X POST http://127.0.0.1:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I reset my password?","session_id":"demo-1"}' | jq
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
  ├→ LLM Provider (streaming SSE response)
  └→ Response → Console
```

Nexus follows a layered design: routers handle channel-specific logic, the orchestrator manages session state and prompt construction, services provide RAG and feedback, and a provider layer abstracts over OpenAI, Anthropic, and Gemini models.

Full architecture and data flow diagrams → [docs/overview.md](docs/overview.md#architecture).

---

## Features

- **Omnichannel** — unified console for chat, copilot, and voice with per-mode message filtering and sync toggle
- **Multi-LLM** — OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0 — switch per agent
- **Live streaming** — SSE delivers tokens word-by-word as the model generates
- **RAG citations** — vector-based retrieval augments every response with source-grounded knowledge
- **Voice (PSTN)** — Twilio, Amazon Connect, generic SIP/CCaaS with STT/TTS pipeline
- **Feedback engine** — CSAT ratings dynamically tune agent temperature and RAG thresholds
- **Encrypted vault** — AES-256-GCM for API keys and integration credentials at rest
- **Session management** — history sidebar, rename, new/clear session
- **iPaaS webhooks** — lifecycle events (session.created, message.completed, feedback.submitted) for n8n/Zapier
- **Dark mode UI** — polished frontend with animations, typing indicator, streaming cursor

---

## Testing

```bash
pytest tests/ --timeout=60 -v                    # 158+ unit tests
pytest tests/test_comprehensive_e2e.py --timeout=120 -v  # 33 E2E tests
ruff check src/ scripts/                          # lint
mypy src/ --ignore-missing-imports                # type check
```

---

## Deployment

| Method | Command |
|--------|---------|
| **Docker** | `docker compose -f deploy/docker/docker-compose.yml up` |
| **Bare metal** | `uvicorn src.main:app --host 0.0.0.0 --port 8001` |
| **CI/CD** | GitHub Actions — lint, test, e2e, docker build, deploy |

---

## Contributing

1. Fork the repo and create a branch from `main`
2. Run tests locally with `pytest tests/`
3. Lint with `ruff check src/ scripts/`
4. Submit a pull request

All contributions — features, bug fixes, docs, tests — are welcome.

---

## License

[MIT](LICENSE) © [Shubham RSY](https://github.com/ShubhamRSY)
