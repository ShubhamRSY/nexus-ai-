## Monitoring (minimal)

### Health checks

- UI/API health: `GET /api/v1/health`

Recommended external uptime probe:

```bash
curl -fsS https://your-domain.com/api/v1/health
```

### Error reporting (Sentry)

Set `SENTRY_DSN` in `config/environment/.env` and restart Nexus.

### Logs

If running with `systemd`:

```bash
sudo journalctl -u nexus -n 200 --no-pager
```

