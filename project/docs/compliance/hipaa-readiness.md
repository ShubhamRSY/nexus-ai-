# HIPAA Readiness Checklist

Nexus provides technical controls to support HIPAA-aligned deployments. **This is not a certification** — execute a BAA and risk assessment with your compliance team.

## Enable HIPAA mode

```env
HIPAA_MODE=true
APP_ENV=production
DATABASE_URL=postgresql://...  # encrypted managed Postgres
```

When `HIPAA_MODE=true`, the platform:

- Logs all PHI-adjacent access to `audit_log` (chat, inbox, portal tickets)
- Disables guest demo login (`ALLOW_GUEST_DEMO=false` recommended)
- Requires authentication on all CX APIs

## Technical safeguards (§164.312)

| Requirement | Nexus control |
|-------------|---------------|
| Access control | JWT + OIDC SSO, RBAC (admin/agent) |
| Audit controls | `audit_log` table, structured logging |
| Integrity | Postgres transactions, migration versioning |
| Transmission security | TLS via Caddy, `DATABASE_URL?sslmode=require` |
| Encryption at rest | Neon/Postgres provider encryption; vault Fernet for secrets |

## Administrative safeguards

- See [soc2/access-controls.md](soc2/access-controls.md)
- See [soc2/key-rotation.md](soc2/key-rotation.md)
- BAA template: contact commercial licensing (`COMMERCIAL_LICENSE.md`)

## Gaps to close before production PHI

- [ ] Sign BAA with cloud providers (Neon, Twilio, OpenAI as applicable)
- [ ] PHI retention policy and automated purge jobs
- [ ] Disable third-party LLM for PHI or use BAAs with providers
- [ ] Annual risk assessment and workforce training records

## Related

- [SOC 2 readiness](soc2-readiness.md)
- [DR runbook](ops-dr-runbook.md)
