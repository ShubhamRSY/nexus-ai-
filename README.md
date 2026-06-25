<div align="center">

# Nexus · Enterprise Voice & Chat AI Platform

**Production-grade omnichannel AI agents for contact centers — chat, voice, and copilot from one runtime.**

[![CI](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/ShubhamRSY/voice-agents/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-158%2B%20unit%20%7C%2033%20E2E%20passing-brightgreen.svg)](tests/)

[Quick Start](#quick-start) · [Features](#features) · [Docs](docs/overview.md)

</div>

---

## What Is Nexus?

Open-source, omnichannel AI agent platform for customer support. One orchestrator routes conversations across chat, copilot, and voice — with RAG, multi-LLM support, and real-time streaming.

| Channel | What it does |
|---------|--------------|
| **Chat** | Live AI conversation with SSE streaming, RAG citations, full session history |
| **Copilot** | Agent-assist — paste a transcript, get an AI-suggested reply |
| **Voice** | PSTN calls via Twilio, Amazon Connect, or any SIP/CCaaS. Live STT, AI TTS. |

> No API key required for local dev. Without `OPENAI_API_KEY`, the platform uses a mock LLM — chat, voice simulator, and all tests still work.

---

## Quick Start

```bash
git clone https://github.com/ShubhamRSY/voice-agents.git
cd voice-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp config/environment/.env.example config/environment/.env
uvicorn src.main:app --reload --port 8001
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001) — the Nexus console.

**Smoke test:**
```bash
curl -s -X POST http://127.0.0.1:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I reset my password?","session_id":"demo-1"}' | jq
```

---

## Features

- **Omnichannel** — chat, copilot, and voice in one console
- **Multi-LLM** — OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0
- **Live streaming** — SSE token-by-token AI responses
- **RAG** — retrieval-augmented generation with source citations
- **Voice (PSTN)** — Twilio, Amazon Connect, generic SIP/CCaaS
- **Feedback engine** — CSAT-driven auto-tuning of agent parameters
- **Encrypted vault** — AES-256-GCM for API keys
- **Sync toggle** — separate or combine conversations per channel
- **Session management** — history sidebar, rename, new/clear session
- **iPaaS webhooks** — lifecycle events for n8n/Zapier

---

## Documentation

| Doc | What's covered |
|-----|---------------|
| [Overview](docs/overview.md) | Architecture, API reference, project tree, environment variables, telephony, feedback loop, agents config |
| [Architecture](docs/technical/ARCHITECTURE.md) | System context, core components, data flow |
| [Integrations](docs/integrations/) | Twilio, CRM, Slack setup guides + iPaaS templates |

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
| **CI/CD** | GitHub Actions — lint, test, e2e, docker build |

---

## Security

- Credentials AES-256-GCM encrypted at rest in the Integrations Vault
- JWT authentication with configurable expiry
- Pydantic input validation on all endpoints
- Strict CORS origin whitelist

---

<div align="center">

**MIT License** · [Shubham RSY](https://github.com/ShubhamRSY)

</div>
