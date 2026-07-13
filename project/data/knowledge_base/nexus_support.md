# Nexus Cloud — Product Knowledge Base

## Getting started

Q: What is Nexus?
A: Nexus is an AI customer experience platform. One engine for chat, voice, email, WhatsApp, SMS, Messenger, Instagram, and Agent Copilot — with 62 integrations, a RAG knowledge layer, and Nexus Cloud hosting so teams can start free without managing servers.

Q: What makes Nexus different?
A: Nexus is omnichannel from day one (not one-channel-only bots), has $0 per-agent fees on the free tier, supports multi-LLM (GPT-4o, Claude, Gemini) without lock-in, and is enterprise-ready with JWT multi-tenant security, analytics, and private deployment options. Every conversation deserves to feel human.

Q: How do I start free?
A: Open https://yournexus.duckdns.org/signup — no credit card. Free includes 2 AI agents, Chat + Email channels, and 5 integrations. Upgrade via /contact when you need Voice, WhatsApp, SMS, or all 62 integrations.

Q: What channels does Nexus support?
A: Nexus supports 8 channels: Web Chat, Agent Copilot, Voice (PSTN), Email, WhatsApp, SMS, Facebook Messenger, and Instagram DMs. All channels share the same AI orchestrator and guardrails.

Q: How many integrations does Nexus have?
A: Nexus ships 62 native integrations spanning CRM (HubSpot, Salesforce), ticketing (Zendesk, Freshdesk, Jira), telephony (Twilio), messaging (Slack, Teams), and more. Credentials are encrypted in a per-workspace vault.

## Account & access

Q: How do I reset my password?
A: On the Nexus login page, click Forgot Password, enter your work email, and follow the reset link (expires in 1 hour). New passwords must be at least 8 characters with a number and a special character. If no email arrives, check spam or contact hello@nexus.com.

Q: How do I add team members?
A: Admins invite teammates from Settings > Team. Choose Admin, Member, or Viewer roles. Plan limits control how many seats you can add. Invitees receive an email join link.

Q: Why am I getting a 403 Forbidden error?
A: A 403 means your request lacks permission. For the API, confirm your API key is valid and sent in the X-API-Key header. For the console, confirm you are signed in and your role allows the action. If using SSO, re-login and ask your admin to check role mapping.

Q: Why is the platform running slowly?
A: Clear browser cache, check network speed, reduce concurrent API calls, and close unused tabs. Nexus Cloud runs on a lean demo VM — heavy concurrent chat can slow responses. For sustained production load, enquire about a larger Always Free Oracle shape or enterprise hosting at hello@nexus.com.

## Billing & plans

Q: When is my billing date?
A: Nexus Free is $0/month. Paid Starter and Growth tiers are billed monthly from signup; annual plans bill on anniversary. Exact dollar pricing is by enquiry — open /pricing or /contact for a quote.

Q: How do I request a refund?
A: For paid plans, request a refund within 30 days (annual) or 7 days (monthly) by emailing hello@nexus.com with your account email and reason. Refunds typically post in 5–7 business days to the original payment method.

Q: What happens if a payment fails?
A: We notify you by email and retry up to 3 times over 5 days. Your workspace stays active during the grace period. After that, paid features may lock until billing is updated in Settings > Billing.

Q: What happens when I upgrade or downgrade my plan?
A: Upgrades take effect immediately with prorated charges. Downgrades apply at the end of the current cycle. Match usage to new agent/channel/integration limits before downgrading. Enterprise changes go through sales via /contact.

## Orders & delivery (demo scenarios)

Q: Where is my order?
A: In this Nexus demo there is no live Shopify/WooCommerce storefront connected yet. For a real customer deployment you would connect your order system under Integrations, then ask for an order number so the agent can look it up. For this demo, say you want a product FAQ — try "What makes Nexus different?" or "How do I start free?"

Q: How do I track my order?
A: Order tracking requires a connected commerce or fulfillment integration (for example Shopify). Once connected, provide your order ID and the agent can retrieve status and tracking. On this demo workspace, connect Shopify from Integrations and add your credentials — until then ask about Nexus plans, channels, or password reset.

Q: How do I cancel my order?
A: Cancellation policies come from your commerce system once integrated. Without a connected order database, Nexus cannot cancel a real order. Connect Shopify/WooCommerce or your OMS, then ask again with the order number. Meanwhile I can explain Nexus Free vs Growth plans if that helps.

## Product & reliability

Q: Is the service down?
A: Check https://yournexus.duckdns.org/landing and /api/v1/health. If both load, Nexus Cloud is up. Temporary slowdowns on the demo VM are usually memory pressure, not a full outage. Email hello@nexus.com if health fails for more than a few minutes.

Q: What AI models does Nexus use?
A: By default Nexus uses GPT-4o-mini for chat and voice agents, with Claude and Gemini as alternatives you can assign per agent. Without API keys the console runs in offline mock mode using the knowledge base FAQ so demos still work.

Q: Can I use my own LLM API key?
A: Yes. Add OpenAI, Anthropic, or Gemini keys under Settings > Integrations. Keys are encrypted at rest and never returned in API responses. You can switch providers per agent. Without keys, Nexus uses mock mode grounded in this knowledge base.

Q: Does Nexus support SSO?
A: Yes. Enterprise plans support SAML 2.0 and OIDC (Okta, Azure AD, Google Workspace, OneLogin). Configure under Settings > Security > Single Sign-On, or enquire via /contact for enterprise setup.

Q: What is the API base URL?
A: Production API base URL: https://yournexus.duckdns.org/api/v1. Health probe: GET /api/v1/health. OpenAPI docs are available at /docs in non-production environments.

Q: What are the API rate limits?
A: The Nexus API allows about 1,000 requests per minute on enterprise plans and 100 on standard/demo tiers, applied per API key or IP. Exceeded calls return HTTP 429 — use exponential backoff with jitter. Contact hello@nexus.com to raise limits.

Q: How do I contact Nexus Support?
A: Email hello@nexus.com, use the console Chat, or send an enquiry at https://yournexus.duckdns.org/contact. For partnership or enterprise pricing, prefer /contact so we can match the right plan.
