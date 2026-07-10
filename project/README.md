<div align="center">

<img src="static/nexus-logo.svg" alt="Nexus" width="72" height="72" />

# Nexus

### *Every conversation deserves to feel human.*

**Purpose-built AI agents. One CX platform.**

**[Try live demo →](https://yournexus.duckdns.org/)** · **[Start free](https://yournexus.duckdns.org/signup)** · **[Send enquiry](https://yournexus.duckdns.org/contact)**

Nexus is a proprietary omnichannel AI platform for customer experience teams — one orchestrator for **Chat**, **Copilot**, **Voice**, **Email**, **WhatsApp**, **SMS**, **Messenger**, and **Instagram**, grounded with **RAG**, protected by **JWT auth + guardrails**, and built for teams who care about every customer moment.

[![CI](https://github.com/ShubhamRSY/nexus-ai-/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/ShubhamRSY/nexus-ai-/actions/workflows/ci-cd.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Proprietary](https://img.shields.io/badge/License-Proprietary-purple.svg)](project/static/legal/licensing.html)
[![Tests](https://img.shields.io/badge/tests-215%2B%20passing-brightgreen.svg)](project/tests/)

</div>

**Live:** [https://yournexus.duckdns.org/](https://yournexus.duckdns.org/) — chat, copilot, voice, RAG, JWT auth, and enterprise integrations.

**Pricing:** not listed publicly — [request a quote](https://yournexus.duckdns.org/contact).

---

## Table of Contents

- [What Is Nexus?](#what-is-nexus)
- [Nexus Concepts](#nexus-concepts)
- [Recent Changes](#recent-changes)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Architecture](#architecture)
- [Features](#features)
- [API Overview](#api-overview)
- [Testing](#testing)
- [Contributing](#contributing)
- [Keeping `main` Safe](#keeping-main-safe)
- [License](#license)

---

## What Is Nexus?

Customer experience (CX) teams lose time and accuracy when chat, voice, and internal tooling live in separate silos. Nexus solves this with a single AI-powered runtime that can resolve interactions, assist frontline agents, and improve operations — all from one console and one orchestration engine.

**Eight channels, one engine:**

| Channel | Purpose |
|---------|---------|
| **Chat** | Live AI conversation with SSE streaming, WebSocket streaming, RAG citations, full session history |
| **Copilot** | Agent-assist — paste a transcript, get an AI-suggested reply |
| **Voice** | PSTN calls via Twilio, Amazon Connect, or any SIP/CCaaS. Live STT, AI TTS |
| **Email** | SMTP outbound + inbound webhook with AI auto-reply in the customer's language |
| **WhatsApp** | Two-way messaging via Twilio WhatsApp Business API |
| **SMS** | Two-way SMS via Twilio Programmable Messaging |
| **Messenger** | Facebook Messenger via Meta Graph API with AI reply |
| **Instagram** | Instagram Direct via Meta Graph API with AI reply |

> **No API key required.** Without `OPENAI_API_KEY`, Nexus falls back to a mock LLM — the console, voice simulator, smoke tests, and all unit tests work immediately.

**What we do (and how it transforms CX)**

- **AI Agents for Customers**: resolve customer inquiries end-to-end across chat and voice — from intake and authentication to execution and follow-up.
- **AI Agents for Frontline Teams (Copilot)**: guide interactions in real time with the right context, next-best actions, and draft responses that reduce handle time and errors.
- **AI Agents for Operations**: evaluate interactions, surface insights, and enable continuous improvement (quality + safety) across both human and AI agents.

**AI-driven outcomes**

- **Faster, better resolutions**: always-on support with consistent answers grounded in your knowledge base.
- **Speed + accuracy + consistency**: reduce errors and handle time with copilot assistance and guardrails.
- **Operate CX with full visibility**: health, logs, analytics, and (optional) observability integrations to continuously improve performance.

---

## Nexus Cloud (hosted SaaS)

Nexus Cloud is **live** at [/signup](https://yournexus.duckdns.org/signup) — self-serve free tier (chat + email), legal acceptance (ToS + Privacy), and optional Stripe billing for paid plans.

**Licensing**

- **Nexus Cloud**: proprietary hosted service — [request pricing](https://yournexus.duckdns.org/contact)
- **Enterprise**: private deployment, SSO, compliance — [contact sales](https://yournexus.duckdns.org/contact?plan=enterprise)

**Hosted features (live now)**

- **Nexus Cloud sign-up** — tenant + admin + subscription + starter KB in ~60s
- **Legal pages** — `/legal/terms`, `/legal/privacy` (required at sign-up)
- **Enterprise CX** — inbox, analytics, tickets, workflows, IVR, supervisor tools, customer portal
- OIDC SSO (Auth0) + JWT auth, encrypted integrations vault, **62 native connectors** ([`/integrations`](https://yournexus.duckdns.org/integrations)), daily backups

**Enterprise add-ons** (docs + API; contact for dedicated infra)

- HIPAA BAA, multi-region HA, dedicated per-tenant VMs

**Branding**

- The **Nexus** name/logo/branding are trademarks. See [`TRADEMARKS.md`](TRADEMARKS.md).

Docs: [`docs/saas-hosted.md`](docs/saas-hosted.md) · [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md)

---

## Nexus Concepts

Nexus is organized around a small set of primitives so you can reason about the system (and extend it safely) without needing to learn every file at once.

**Core primitives**

- **Orchestrator**: The brain of the runtime. It receives a user event (chat message, copilot transcript, or voice turn), loads session context, retrieves relevant knowledge, selects an agent policy, and streams back tokens.
- **Agents**: Configured behaviors (prompts + tools + routing rules). An agent can be specialized (billing, refunds, troubleshooting) or general-purpose, and can be swapped per request.
- **Channels**: Transport + UX mode. Channel adapters normalize inputs/outputs so the orchestrator sees a consistent event shape while each channel keeps its own streaming protocol and pacing.
  - **Chat**: JSON response or streaming via SSE/WS
  - **Copilot**: transcript → suggested reply (agent-assist)
  - **Voice**: streaming STT → LLM → TTS (telephony provider integration)
- **Knowledge base (RAG)**: A document store + embeddings + retrieval step that grounds responses in your internal docs. Nexus attaches citations so answers can be audited.
- **Guardrails**: Safety and reliability layers around generation: rate limits, auth, tool allowlists, prompt constraints, and (optionally) secrets resolution via Vault.
- **State & storage**: Session history and metadata stored in SQLite (dev) or Postgres (prod), with Redis used for caching and queueing.

**What “Nexus” means in practice**

- **One runtime for all channels**: you do not maintain separate “chat bot” and “voice bot” codepaths with divergent prompt logic.
- **Consistent observability**: streaming, errors, and latency can be traced per session across channels.
- **Safe extension points**: most customization should happen by adding/adjusting agents, tools, and KB content rather than editing request plumbing.

---

## Recent Changes

### v2.5.1 — Brand & dark marketing UI (July 2026)

| Change | Description |
|--------|-------------|
| **Nexus brand** | Logo, tagline (*Every conversation deserves to feel human.*), and emotional copy across landing, contact, pricing, FAQ, and integrations |
| **Dark UI** | Glass enquiry forms, feature panels (no tiny screenshots), integration logos via Simple Icons CDN |
| **Proprietary positioning** | Public pricing removed — request quote via [`/contact`](https://yournexus.duckdns.org/contact) (`hello@nexus.com`) |
| **README** | Brand header, tagline, and updated SaaS/enquiry links at the top |

### v2.5.0 — 62 native integrations + SaaS pricing (July 2026)

| Change | Description |
|--------|-------------|
| **62 native integrations** | CRM, ticketing, CCaaS, telephony, BI, HRIS, knowledge, and more — each with vault credentials, status API, and proxy routes |
| **Integrations catalog** | Public page at [`/integrations`](https://yournexus.duckdns.org/integrations) with search and category filters |
| **Nexus Cloud plans** | Free / Starter / Growth / Enterprise — enquire for paid tiers; see [`docs/saas-hosted.md`](docs/saas-hosted.md) |
| **Production security** | Required `POSTGRES_PASSWORD` / `REDIS_PASSWORD`, CORS wildcard blocked in prod, Redis auth, CI Bandit + pip-audit, staging deploy on `develop` |
| **LinkedIn deck** | `exports/linkedin/Nexus_LinkedIn_Launch.pdf` — 4K retina screenshots; upload PDF (not PPTX) |
| **QA verified** | 215+ tests passing (unit, integration, E2E with live server); all integration routes return mock-safe responses without credentials |

### v2.4.0 — Deploy + dark deck (July 2026)

| Change | Description |
|--------|-------------|
| **Production deploy** | SaaS, legal, CX/enterprise features on yournexus.duckdns.org |
| **LinkedIn deck** | `exports/linkedin/Nexus_LinkedIn_Launch.pdf` — upload **PDF** to LinkedIn (not PPTX; PPTX blurs). Build: `capture_mode_screenshots.py` → `build_linkedin_ppt.py` |
| **E2E verified** | Tests passing (unit + integration + live server) |

### v2.3.2 — Production blockers fixed (July 2026)

| Change | Description |
|--------|-------------|
| **RAG / HF cache** | Auto-fix invalid `HF_HOME` paths (e.g. `/Volumes/<YourDriveName>`); hash fallback if model load fails |
| **Vault diagnostics** | `/health` reports `vault.decrypt_ok` — fix `INTEGRATIONS_ENCRYPTION_KEY` mismatch |
| **Legal** | `/legal/terms`, `/legal/privacy`, `/legal/licensing` — required on SaaS sign-up |
| **Commercial license** | Published pricing: Startup $12k, Growth $36k, Enterprise from $96k/yr |
| **Restart script** | `bash scripts/restart_local.sh` after deploy |

### v2.3.1 — Live SaaS sign-up (July 2026)

| Change | Description |
|--------|-------------|
| **Public sign-up** | [/signup](https://yournexus.duckdns.org/signup) — plan picker + instant workspace provisioning |
| **Provisioning** | Auto-creates tenant, admin, subscription, starter KB |
| **Stripe optional** | Checkout + webhook when `STRIPE_SECRET_KEY` is set; otherwise 14-day trial |
| **API** | `POST /api/v1/saas/signup`, `GET /api/v1/saas/signup/config` |

### v2.3.0 — Enterprise contact center (July 2026)

| Change | Description |
|--------|-------------|
| **Nexus Cloud (SaaS)** | Plans API, subscription management, [hosted SaaS docs](docs/saas-hosted.md) |
| **Visual IVR designer** | Drag-style flow builder, stored flows, Twilio execution engine |
| **Mobile SDK** | iOS Swift + Android Kotlin + embeddable web widget (`sdk/`) |
| **Customer portal** | `/portal` — KB search, ticket submit/track, co-browse |
| **HIPAA readiness** | `HIPAA_MODE` flag + [compliance checklist](docs/compliance/hipaa-readiness.md) |
| **Multi-region HA** | `GET /api/v1/ha/status`, peer health checks, failover config |
| **Co-browsing** | WebSocket relay + screen-share hooks for agent assist |
| **Supervisor tools** | Monitor, whisper, barge on live sessions |
| **Quality management** | QM review queue, rubric scoring, review workflows |
| **Agent status** | Available/away/break/offline team dashboard + heartbeat |

### v2.2.0 — Full CX platform (July 2026)

| Change | Description |
|--------|-------------|
| **Agent inbox** | Human handoff queue with claim, reply, and resolve — hybrid AI + agent model |
| **Analytics dashboard** | KPIs + avg response time, volume chart, CSAT, NPS, thumbs-up rate, agent scorecard |
| **Email channel** | SMTP outbound + inbound webhook with AI auto-reply |
| **WhatsApp / SMS / Messenger / Instagram** | Twilio + Meta Graph API inbound with AI reply in customer language |
| **Ticketing UI** | Full ticket list with status management; syncs to HubSpot, Zendesk, and Jira |
| **CSAT + NPS + thumbs** | Session-end survey + per-message 👍/👎 on every AI reply |
| **Translation** | Auto-detect locale; replies translated back to customer language |
| **Workflow builder** | Visual trigger → condition → action flows with runtime execution |
| **Try-it-now demo** | One-click sandbox login (`POST /api/v1/auth/demo-login`) on the login screen |

### v2.1.0 — Enterprise pilot (July 2026)

| Change | Description |
|--------|-------------|
| **Live production** | Deployed at [yournexus.duckdns.org](https://yournexus.duckdns.org/) (Oracle Cloud VM + Caddy + systemd) |
| **PostgreSQL (Neon)** | Managed Postgres in production (`DATABASE_URL`); SQLite remains default for local dev |
| **OIDC SSO** | Auth0 integration with JIT provisioning, role mapping, audit logging — [setup guide](docs/ops-oidc-auth0.md) |
| **Observability** | Request/latency/5xx/auth metrics middleware; Prometheus + JSON health dashboards |
| **Reliability** | Daily backup timer, restore-drill script, RPO/RTO runbook |
| **SOC 2 prep** | Evidence checklist, access-control policy template, key-rotation procedures |
| **Load testing** | k6 smoke script with performance budgets — [docs](docs/ops-load-testing.md) |
| **HA roadmap** | Multi-region / Postgres HA architecture doc for future scale — [docs](docs/ha-multi-region.md) |

### v2.0.0 — Production Hardening (June 2026)

| Change | Description |
|--------|-------------|
| **HTTPS/TLS** | Caddy reverse proxy with auto-HTTPS (Let's Encrypt), security headers, edge rate limiting |
| **PostgreSQL + Redis** | Docker Compose with Postgres 16 (connection pooling), Redis 7, health checks, persistent volumes |
| **Rate limiting** | Redis-backed sliding window with in-memory fallback, per-endpoint-group limits |
| **CI with PostgreSQL** | CI runs tests against both SQLite and PostgreSQL; conditional LLM E2E tests |
| **Zero-downtime deploys** | Gunicorn with preload, max-requests, graceful SIGHUP reload, config file |
| **Structured logging** | File sink with rotation, Loki push support, JSON output for production |
| **Secrets management** | HashiCorp Vault integration (optional, via `hvac`), layered credential resolution |
| **Automated backups** | Backup script for PostgreSQL + ChromaDB with S3 upload, retention, cron scheduling |
| **Load testing config** | 15 benchmark scenarios, concurrency profiles, performance budgets in `benchmarks.json` |
| **Dependencies pinned** | All 28 runtime deps pinned to exact versions; ruff + mypy in dev group |
| **Dockerfile optimized** | Multi-stage build -> gunicorn config, COPY safety, non-root user |
| **109+ tests** | Full coverage: unit, integration, E2E, non-functional, security, concurrency |

---

## Prerequisites

- **Python 3.11+**
- **pip** (bundled with Python)
- **git**
- *(Optional)* An [OpenAI](https://platform.openai.com/api-keys), [Anthropic](https://console.anthropic.com/), or [Google Gemini](https://ai.google.dev/) API key for production LLM access
- *(Optional)* [Docker](https://www.docker.com/) + [Docker Compose](https://docs.docker.com/compose/) for containerized deployment

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ShubhamRSY/voice-agents.git
cd voice-agents/project

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Copy the environment template (no edits needed to start)
cp config/environment/.env.example config/environment/.env

# Optional: enable demo users and sample KB for local exploration
# echo "DEMO_MODE=true" >> config/environment/.env

# 5. Start the server
uvicorn src.main:app --reload --port 8001
```

Open **[http://127.0.0.1:8001](http://127.0.0.1:8001)** — the Nexus console loads with a welcome screen, session sidebar, and channel selector.

If you deployed to a VM, open your production console URL (example): **[https://yournexus.duckdns.org/](https://yournexus.duckdns.org/)**.

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

---

## Production Deployment

### Production readiness

| Area | Status | Notes |
|------|--------|-------|
| **Core product** | Ready | Chat, copilot, voice, email, WhatsApp, SMS, Messenger, Instagram, RAG, CX platform |
| **Auth** | Ready | JWT + Auth0 OIDC SSO |
| **Database** | Ready | Neon PostgreSQL in production; SQLite for local dev |
| **TLS / edge** | Ready | Caddy + Let's Encrypt |
| **Backups & DR** | Ready | Daily timer + restore drill; Neon handles DB backups |
| **Monitoring** | Ready | Uptime alerts + in-app observability |
| **Enterprise CX** | Ready | Agent inbox, analytics, ticketing, workflows, IVR, supervisor, QM, co-browse, customer portal |
| **SaaS** | Ready | Sign-up flow, subscription plans, Stripe billing, tenant provisioning |
| **HIPAA readiness** | Ready | HIPAA_MODE flag, PHI logging, compliance checklist |
| **Multi-region HA** | Ready | Peer health checks, failover config, read replica support |
| **SOC 2 audit** | Prep only | Checklist + policies — formal audit is future work |

**Tier B (paying SMB customers) — optional next:** Redis (Upstash), S3 offsite backups for Chroma/config, custom domain, k6 load test, staging env.

### Managed PostgreSQL (Neon) on a small VM

For VMs with limited RAM (~512 MB), run Postgres **off the VM** instead of installing it locally:

1. Create a project at [neon.tech](https://neon.tech) and copy the connection string.
2. Set `DATABASE_URL=postgresql://...?sslmode=require` in `config/environment/.env`.
3. Restart Nexus — migrations run automatically on startup.
4. Register the **first admin** (empty database) or sign in via SSO (JIT provisioning).

The app uses a PostgreSQL compatibility layer in `src/database.py` so the same CRUD code works with SQLite (dev) and Postgres (prod).

### Docker Compose (recommended)

```bash
# Full stack with TLS, Postgres, Redis
docker compose -f deploy/docker/docker-compose.yml up

# Include automated backups
docker compose -f deploy/docker/docker-compose.yml --profile backup up
```

**Free hosting ($0/month):** See [docs/deploy-oracle-duckdns.md](docs/deploy-oracle-duckdns.md) for Oracle Cloud + DuckDNS step-by-step.

This starts:
- **Caddy** — TLS termination, rate limiting, security headers, JSON access logs
- **PostgreSQL 16** — persistent volume, health checks, auto-extensions
- **Redis 7** — persistent volume, caching + task queue
- **Nexus** — gunicorn with 2-4x CPU workers, max-requests, graceful reload
- **Backup** (profile) — daily PostgreSQL + ChromaDB backup to local or S3

### Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOMAIN` | No | `:80` | Domain for auto-HTTPS (set to `nexus.example.com` in prod) |
| `DATABASE_URL` | No | SQLite (local) | `postgresql://...` — use [Neon](https://neon.tech) or Docker Postgres |
| `REDIS_URL` | No | in-memory | `redis://host:6379/0` |
| `OPENAI_API_KEY` | No | mock | LLM provider key |
| `SENTRY_DSN` | No | — | Error tracking |
| `OTEL_ENDPOINT` | No | — | OpenTelemetry collector |
| `VAULT_ADDR` | No | — | HashiCorp Vault URL |
| `CORS_ORIGINS` | No | `*` | Set to your domain in production |
| `APP_ENV` | No | `development` | Set to `production` to disable docs and demo reset |
| `AUTH_REQUIRED` | No | `false` | Set to `true` in production |
| `DEMO_MODE` | No | `false` | Set to `true` for local demo users/KB |
| `BACKUP_S3_BUCKET` | No | — | S3 bucket for offsite backups |

Full reference: [`config/environment/.env.example`](config/environment/.env.example)

### Bare Metal

```bash
# Install production dependencies
pip install -e "."

# Set environment variables (see .env.example)
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...

# Start with gunicorn (zero-downtime)
gunicorn src.main:app --config deploy/docker/gunicorn.conf.py

# Graceful reload (zero-downtime)
kill -HUP <gunicorn-pid>
```

---

## Architecture

```
                          ┌─────────────┐
                          │   Caddy     │  ← TLS termination, rate limiting
                          │  (reverse   │
                          │   proxy)    │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │   FastAPI   │  ← Auth, CORS, tenant, rate limit middleware
                          │   (Nexus)   │
                          └──┬───┬───┬──┘
                             │   │   │
              ┌──────────────┤   │   ├──────────────┐
              │              │   │   │              │
       ┌──────▼──────┐ ┌────▼───▼───▼────┐ ┌───────▼──────┐
       │   Chat      │ │   Orchestrator  │ │   Voice      │
       │   Copilot   │ │  (LangGraph)    │ │  (Twilio)    │
       │   SSE/WS    │ │  RAG + Guardrails│ │  STT/TTS     │
       └──────┬──────┘ └────┬───┬───┬────┘ └──────┬───────┘
              │             │   │   │              │
              └─────────────┘   │   └──────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼────┐ ┌───▼───┐ ┌─────▼────┐
              │ Postgres │ │ Redis │ │ ChromaDB │
              │ (SQLite  │ │(cache+│ │ (vector  │
              │   dev)   │ │queue) │ │  store)  │
              └──────────┘ └───────┘ └──────────┘
```

Nexus follows a layered design: domain routers handle channel-specific logic, the orchestrator manages session state and prompt construction, services provide RAG and feedback, and a provider layer abstracts over OpenAI, Anthropic, and Gemini models.

Full architecture → [docs/overview.md](docs/overview.md#architecture).

---

## Features

### Channels
- **Chat** — SSE streaming, WebSocket streaming, RAG citations, session history, Markdown rendering
- **Voice (PSTN)** — Twilio, Amazon Connect, generic SIP/CCaaS with STT/TTS pipeline, call transfer
- **Email** — SMTP outbound + inbound webhook, AI auto-reply in customer language
- **WhatsApp / SMS** — Two-way messaging via Twilio Messaging API
- **Messenger / Instagram** — Meta Graph API integration with webhook verification
- **Agent Copilot** — paste a transcript, get AI-suggested draft reply, summarization, escalation flags

### AI & Knowledge
- **Multi-LLM** — OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 2.0 — switch per agent
- **RAG** — Vector-based retrieval (ChromaDB) with citations grounded in your knowledge base
- **Translation** — Auto-detect locale, translate replies back to customer language
- **Feedback engine** — CSAT, NPS, thumbs up/down dynamically tune temperature and RAG thresholds

### Agent Experience (CX Platform)
- **Agent inbox** — Human handoff queue with claim, reply, and resolve — hybrid AI + agent model
- **Ticketing** — Full ticket list with status management; syncs to **62 native connectors** (HubSpot, Salesforce, Zendesk, Freshdesk, ServiceNow, Jira, PagerDuty, and more)
- **Analytics dashboard** — KPIs, avg response time, volume chart, CSAT, NPS, thumbs-up rate, agent scorecard
- **Workflow automation** — Visual trigger → condition → action flows with runtime execution
- **Translation** — Auto-detect locale, AI reply in customer language

### Enterprise Contact Center
- **Visual IVR designer** — Drag-style flow builder, stored flows, Twilio execution engine
- **Supervisor tools** — Monitor, whisper, barge on live sessions
- **Quality management** — QM review queue, rubric scoring, review workflows
- **Co-browsing** — WebSocket relay + screen-share hooks for agent assist
- **Agent presence** — Available/away/break/offline team dashboard with heartbeat
- **Customer portal** — KB search, ticket submit/track, co-browse initiation

### Developer & Operations
- **Mobile SDK** — iOS Swift + Android Kotlin + embeddable web widget (`sdk/`)
- **Live streaming** — SSE (`GET /api/v1/chat/sse`) and WebSocket (`ws://.../chat/stream`)
- **Multi-tenant SaaS** — Sign-up flow, subscription plans, Stripe billing, tenant provisioning
- **OIDC SSO** — Auth0 integration with JIT provisioning, role mapping, audit logging

### Integrations & iPaaS
- **62 native connectors** — CRM (HubSpot, Salesforce, Pipedrive, Dynamics 365, Zoho, Copper), ticketing (Zendesk, Freshdesk, Help Scout, Front), CCaaS (Five9, Genesys, NiCE, Talkdesk, Amazon Connect), telephony (Twilio, Zoom, Vonage, RingCentral), BI (Snowflake, BigQuery, Tableau, Power BI, Amplitude), HRIS (Workday, BambooHR, ADP, Gusto), project tools (Jira, Asana, Monday, Linear, Azure DevOps), and more
- **Integrations catalog** — [`GET /integrations`](https://yournexus.duckdns.org/integrations) public UI + `GET /api/v1/integrations/catalog` API
- **Encrypted vault** — AES-256-GCM for all integration credentials at rest
- **iPaaS webhooks** — Lifecycle events for n8n/Zapier alongside native adapters
- **HIPAA readiness** — `HIPAA_MODE` flag, PHI access logging, compliance checklist
- **Multi-region HA** — Peer health checks, failover config, read replica support
- **Production infrastructure** — TLS termination (Caddy), PostgreSQL, Redis, automated backups
- **Dark mode UI** — Polished frontend with animations, typing indicator, streaming cursor

### Enterprise operations (runbooks)

| Milestone | Docs |
|-----------|------|
| M1 — SSO + observability | [OIDC Auth0 setup](docs/ops-oidc-auth0.md) · [Monitoring & alerts](docs/ops-monitoring.md) |
| M2 — DR + load testing | [DR runbook (RPO/RTO)](docs/ops-dr-runbook.md) · [Load testing](docs/ops-load-testing.md) |
| M3 — SOC 2 readiness | [SOC 2 checklist](docs/soc2-readiness.md) · [Access controls](docs/soc2/access-controls.md) · [Key rotation](docs/soc2/key-rotation.md) |
| M4 — HA / multi-region | [HA architecture](docs/ha-multi-region.md) |

Scripts: `scripts/restore-drill.sh` · `scripts/loadtest/k6-smoke.js` · `scripts/setup-backup-timer.sh`

---

## API Overview

### Auth & Identity
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new tenant + admin user |
| POST | `/api/v1/auth/login` | Login, receive JWT |
| GET | `/api/v1/auth/me` | Current user info |
| POST | `/api/v1/auth/demo-login` | One-click demo login |
| GET | `/api/v1/auth/oidc/config` | OIDC SSO enabled flag (public) |
| GET | `/api/v1/auth/oidc/login` | Start OIDC SSO redirect |
| GET | `/api/v1/auth/oidc/callback` | OIDC callback (issues JWT) |
| POST | `/api/v1/admin/users` | Create user (admin) |

### Chat & Copilot
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message, get AI response |
| GET | `/api/v1/chat/sse` | SSE streaming chat (token-by-token) |
| WS | `/api/v1/chat/stream` | WebSocket streaming chat |
| POST | `/api/v1/copilot` | Agent-assist: transcript → suggested reply |
| DELETE | `/api/v1/chat/{session_id}` | End a session |
| GET | `/api/v1/sessions/stats` | Active session count |
| GET | `/api/v1/sessions/{id}/history` | Session message history |

### Voice & Telephony
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/telephony/voice/inbound` | Twilio inbound call webhook |
| POST | `/api/v1/telephony/voice/process` | Twilio call process/gather |
| POST | `/api/v1/telephony/voice/status` | Twilio call status callback |
| POST | `/api/v1/telephony/simulate` | Simulate voice call (dev) |
| GET | `/api/v1/telephony/voice/stream` | SSE voice stream |
| POST | `/api/v1/messaging/inbound` | Twilio messaging inbound (WhatsApp/SMS) |
| POST | `/api/v1/messaging/send` | Send outbound WhatsApp/SMS |

### Knowledge Base & RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/kb/articles` | List KB articles |
| POST | `/api/v1/kb/articles` | Create KB article |
| PUT | `/api/v1/kb/articles/{id}` | Update KB article |
| DELETE | `/api/v1/kb/articles/{id}` | Delete KB article |
| POST | `/api/v1/kb/upload` | Upload document to KB |
| POST | `/api/v1/rag/search` | Search knowledge base |
| POST | `/api/v1/rag/ingest` | Ingest documents into vector store |

### Agent Inbox & Handoff
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inbox` | List escalated conversations |
| POST | `/api/v1/inbox/{id}/claim` | Claim a conversation |
| POST | `/api/v1/inbox/{id}/reply` | Reply as human agent |
| POST | `/api/v1/inbox/{id}/resolve` | Resolve handoff |
| POST | `/api/v1/handoff/{session_id}` | Escalate session to human |

### Ticketing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tickets` | List tickets |
| POST | `/api/v1/tickets` | Create ticket |
| PATCH | `/api/v1/tickets/{id}` | Update ticket status |

### CX Dashboard & Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cx/dashboard` | CX analytics dashboard |
| POST | `/api/v1/csat` | Submit CSAT rating (1-5) |
| GET | `/api/v1/csat/stats` | CSAT statistics |
| POST | `/api/v1/nps` | Submit NPS rating (0-10) |
| GET | `/api/v1/nps/stats` | NPS statistics |
| POST | `/api/v1/messages/{id}/feedback` | Thumbs up/down feedback |

### Workflows & Automation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workflows` | List workflow rules |
| POST | `/api/v1/workflows` | Create workflow rule |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow rule |

### Email
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/email/send` | Send email via SMTP |
| POST | `/api/v1/email/inbound` | Inbound email webhook |

### Meta (Messenger / Instagram)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/meta/webhook` | Meta webhook verification |
| POST | `/api/v1/meta/webhook` | Meta inbound message webhook |

### Translation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/translate` | Auto-detect and translate text |

### Enterprise (IVR, Supervisor, QM, Co-browse)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents/status` | Update agent presence |
| GET | `/api/v1/agents/team` | List team presence |
| GET | `/api/v1/ivr/flows` | List IVR flows |
| POST | `/api/v1/ivr/flows` | Save IVR flow |
| POST | `/api/v1/supervisor/action` | Monitor/whisper/barge |
| GET | `/api/v1/qm/reviews` | List quality reviews |
| POST | `/api/v1/qm/reviews` | Submit quality review |
| POST | `/api/v1/cobrowse/start` | Start co-browsing session |
| WS | `/api/v1/cobrowse/ws/{id}` | Co-browsing WebSocket |

### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/integrations/catalog` | Public catalog (62 native connectors, searchable) |
| GET | `/api/v1/integrations/status` | Provider connection status |
| PUT | `/api/v1/integrations/credentials` | Save encrypted credential |
| DELETE | `/api/v1/integrations/credentials/{key}` | Remove credential |
| POST | `/api/v1/integrations/webhooks` | Register webhook URL |
| DELETE | `/api/v1/integrations/webhooks/{type}` | Remove webhook |
| POST | `/api/v1/integrations/{provider}/…` | 55+ provider proxy routes (Zendesk, Salesforce, PagerDuty, Snowflake, Epic, etc.) |

See [`/integrations`](https://yournexus.duckdns.org/integrations) for the full connector list.

### Customer Portal
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/portal/kb/search` | Search knowledge base |
| POST | `/api/v1/portal/tickets` | Submit support ticket |
| POST | `/api/v1/portal/tickets/lookup` | Look up ticket status |
| GET | `/api/v1/portal/tickets/{id}` | Get ticket details |
| POST | `/api/v1/portal/cobrowse/start` | Start co-browse from portal |

### SaaS / Subscription
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/saas/plans` | List available plans |
| GET | `/api/v1/saas/subscription` | Current subscription |
| POST | `/api/v1/saas/subscribe` | Change subscription |
| POST | `/api/v1/saas/signup` | Sign up new tenant |
| GET | `/api/v1/saas/signup/config` | Sign-up configuration |

### Observability & Ops
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check (no auth) |
| GET | `/api/v1/metrics` | Prometheus metrics |
| GET | `/api/v1/observability/health` | Detailed runtime snapshot |
| GET | `/api/v1/analytics/dashboard` | Conversation analytics |
| GET | `/api/v1/analytics/agents` | Agent scorecard |
| GET | `/api/v1/analytics/timeline` | Hourly volume timeline |
| GET | `/api/v1/feedback/{agent}/report` | Feedback report |
| GET | `/api/v1/feedback/{agent}/suggestions` | Improvement suggestions |
| POST | `/api/v1/events` | Ingest external event |
| GET | `/api/v1/agents` | List configured agents |
| GET | `/api/v1/llm/config` | LLM configuration |
| POST | `/api/v1/evaluation/run` | Run evaluation suite |
| POST | `/api/v1/demo/reset` | Reset demo data |

### Multi-region HA
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ha/status` | HA region health and failover status |

### Frontend Pages
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Agent console (SPA) |
| GET | `/signup` | SaaS sign-up page |
| GET | `/integrations` | Integrations catalog (62 native connectors) |
| GET | `/portal` | Customer self-service portal |
| GET | `/legal/terms` | Terms of service |
| GET | `/legal/privacy` | Privacy policy |
| GET | `/legal/licensing` | Commercial licensing info |

Full reference at `/docs` when the server is running.

---

## Testing

```bash
# Unit & integration (server not required) — 123+ tests
pytest tests/ -q --ignore=tests/test_comprehensive_e2e.py --ignore=tests/e2e

# E2E journeys — 32+ tests
pytest tests/e2e/ -q

# Live E2E (requires server on :8001) — 60+ tests
bash scripts/restart_local.sh   # terminal 1
pytest tests/test_comprehensive_e2e.py -v

# Full CI pipeline locally
bash scripts/ci.sh

# Lint + type check
ruff check src/ scripts/
mypy src/
```

**Last QA run (July 2026):** 215+ tests passing; chat, signup, auth, and all 55 integration proxy routes verified on live server (mock mode, no 5xx).

---

## Contributing

1. Fork the repo and create a branch from `main`
2. Run tests locally with `pytest tests/`
3. Lint with `ruff check src/ scripts/`
4. Run type check with `mypy src/`
5. Submit a pull request

All contributions — features, bug fixes, docs, tests — are welcome.

---

## Keeping `main` Safe

If you’re collaborating (or deploying from this repo), these practices help prevent accidental breakage and secret leaks.

**Branch protection (recommended)**

- Protect `main` and require PRs (no direct pushes).
- Require status checks to pass (CI / tests / lint / typecheck).
- Require at least 1 review approval (2 for risky areas like auth, billing, deployments).
- Enable “Require branches to be up to date before merging”.
- Prefer “Squash and merge” to keep history readable.

**CI as the gate**

- Keep `scripts/ci.sh` (or the CI workflow) as the single source of truth for what must pass before merge.
- Add new checks there first (then mark them required in branch protection).

**Secrets hygiene**

- Never commit `.env` files. Use `config/environment/.env.example` as the source of truth.
- Treat production credentials as external (Vault, secret manager, or CI secrets) — not repo files.
- If you suspect a key leaked: revoke/rotate immediately, then purge from git history (do not rely on “delete the file”).

**Safer local development**

- Use the mock LLM by default (no `OPENAI_API_KEY`) when iterating on routing and UI.
- Develop features behind config flags when possible, so `main` remains deployable.

---

## License

[AGPL-3.0](LICENSE) © [Shubham RSY](https://github.com/ShubhamRSY)
