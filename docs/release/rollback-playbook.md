# Rollback Playbook

## Decision: Rollback vs Hotfix?

| Situation | Strategy |
|-----------|----------|
| Broken deploy, previous version was stable | **Rollback** |
| Bug found but previous version also had issues | **Hotfix** |
| Data migration was applied (DB schema changed) | **Hotfix** (rollback may lose data) |
| Security vulnerability in the new release | **Rollback** + hotfix in parallel |

## Rollback Procedure — Docker Compose

### 1. Identify the last known good version

```bash
# List available tags
docker image ls ghcr.io/scub-france/docling-studio --format '{{.Tag}}' | sort -V

# Or check GitHub releases
gh release list --repo scub-france/Docling-Studio
```

### 2. Pin the image to the previous version

Edit `docker-compose.yml` or `docker-compose.override.yml`:

```yaml
services:
  backend:
    image: ghcr.io/scub-france/docling-studio:0.2.0-remote  # pin to last good
  frontend:
    image: ghcr.io/scub-france/docling-studio:0.2.0-remote
```

### 3. Restart

```bash
docker compose down
docker compose up -d --wait
```

### 4. Verify

```bash
curl -s http://localhost:3000/api/health | jq .
# Confirm version matches the rolled-back version
```

### 5. Communicate

- Notify the team that a rollback was performed
- Open an issue describing the failure
- Link the failed release and the rollback commit

## Rollback Procedure — Hugging Face Space

1. Use `git revert` on the HF Space repo to revert to the previous commit
2. Or re-upload the previous version: `huggingface-cli upload <space-id> . . --repo-type space --revision <previous-commit>`
3. Verify the app loads correctly

## Database Considerations

Docling Studio uses **SQLite** with a file-based database. Key points:

- **No schema migrations** are applied automatically — the schema is created on first run
- If a new release adds columns, rolling back may cause "unknown column" errors
- **Before deploying a release that changes the DB schema**: back up the SQLite file

```bash
# Backup before deploy
cp data/docling-studio.db data/docling-studio.db.bak-$(date +%Y%m%d)

# Restore after rollback
cp data/docling-studio.db.bak-YYYYMMDD data/docling-studio.db
```

## Post-Rollback

1. Keep the rollback in place until the root cause is identified
2. Fix the issue on a `hotfix/*` branch
3. Re-run the [release audit](../audit/master.md) on the fix
4. Re-deploy following the [deployment checklist](deployment-checklist.md)
