# Deployment Checklist

Checklist for deploying a new release of Docling Studio. Applies to both self-hosted and Hugging Face Space deployments.

## Pre-Deploy

- [ ] Release branch merged to `main` via PR
- [ ] Git tag `vX.Y.Z` created on `main`
- [ ] Release audit passed (score >= 80, 0 CRITICAL) — see [docs/audit/master.md](../audit/master.md)
- [ ] `CHANGELOG.md` section finalized with release date
- [ ] `frontend/package.json` version matches the tag
- [ ] All CI checks green on the tagged commit
- [ ] Docker images built and pushed to `ghcr.io`:
  - `X.Y.Z-remote`, `X.Y.Z-local`
  - `X.Y-remote`, `X.Y-local`
  - `latest-remote`, `latest-local`

## Deploy — Self-Hosted (Docker Compose)

- [ ] Pull the new image:
  ```bash
  docker compose pull
  ```
- [ ] Check environment variables (`.env` or `docker-compose.override.yml`):
  - `CONVERSION_ENGINE` (local / remote)
  - `RATE_LIMIT_RPM`
  - `MAX_FILE_SIZE_MB`
  - `MAX_CONCURRENT_ANALYSES`
- [ ] Start the stack:
  ```bash
  docker compose up -d --wait
  ```
- [ ] Verify health endpoint:
  ```bash
  curl -s http://localhost:3000/api/health | jq .
  # Expected: {"status":"ok","engine":"...","version":"X.Y.Z","deploymentMode":"self-hosted"}
  ```

## Deploy — Hugging Face Space

- [ ] Upload to HF Space via `huggingface-cli`:
  ```bash
  huggingface-cli upload <space-id> . . --repo-type space
  ```
- [ ] Set environment variables in HF Space settings
- [ ] Wait for build to complete in HF Space logs
- [ ] Verify the app loads and health endpoint returns correct version

## Post-Deploy Smoke Test

- [ ] Home page loads
- [ ] Upload a PDF — document appears in the list
- [ ] Run an analysis — completes without error
- [ ] View results — markdown, HTML, bbox overlays render correctly
- [ ] Download results
- [ ] If local mode: test chunking
- [ ] Check `/api/health` returns the new version

## Rollback Triggers

Rollback immediately if any of these occur:

| Trigger | Action |
|---------|--------|
| Health endpoint returns error or wrong version | Rollback |
| Upload or analysis fails on a previously working PDF | Rollback |
| Frontend shows blank page or JS errors | Rollback |
| Error rate > 5% in the first 15 minutes | Rollback |

For rollback procedure, see [rollback-playbook.md](rollback-playbook.md).
