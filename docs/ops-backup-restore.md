## Backups (SQLite + Chroma)

This deployment can run with:

- **SQLite** (default when `DATABASE_URL` is empty)
- **Chroma** persisted to `data/chroma`

### Create a backup (manual)

From the repo root:

```bash
BACKUP_DIR=~/backups ./scripts/backup.sh
```

Artifacts:

- `nexus-sqlite-<timestamp>.db`
- `nexus-chroma-<timestamp>.tar.gz`
- `nexus-config-<timestamp>.tar.gz`

### Restore (manual)

1. Stop Nexus.
2. Restore SQLite:

```bash
cp -f /path/to/nexus-sqlite-<timestamp>.db ./data/nexus.db
```

3. Restore Chroma:

```bash
rm -rf ./data/chroma
tar xzf /path/to/nexus-chroma-<timestamp>.tar.gz -C ./data
```

4. Start Nexus and verify:

```bash
curl -s http://127.0.0.1:8001/api/v1/health
```

