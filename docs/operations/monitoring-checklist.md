# Monitoring Checklist

What to monitor in a Docling Studio deployment.

## Health Endpoint

The primary monitoring signal is the health endpoint:

```bash
curl -s http://localhost:3000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "engine": "local",
  "version": "0.3.0",
  "deploymentMode": "self-hosted"
}
```

**Alert if**: status != "ok", endpoint unreachable, or response time > 5s.

## Four Golden Signals

### 1. Latency

| Endpoint | Expected | Alert threshold |
|----------|----------|-----------------|
| `GET /api/health` | < 100ms | > 1s |
| `POST /api/documents` (upload) | < 2s | > 10s |
| `POST /api/analyses` (create) | < 500ms (queuing only) | > 5s |
| `GET /api/analyses/:id` (results) | < 500ms | > 3s |

### 2. Traffic

| Metric | What to watch |
|--------|---------------|
| Requests per minute | Baseline for normal usage |
| Uploads per hour | Capacity planning |
| Concurrent analyses | Should stay <= `MAX_CONCURRENT_ANALYSES` |

### 3. Errors

| Signal | Alert threshold |
|--------|-----------------|
| HTTP 5xx rate | > 1% of requests |
| Analysis failure rate | > 10% of analyses |
| Rate limit hits (429) | Spike = possible abuse |

### 4. Saturation

| Resource | Check command | Alert threshold |
|----------|---------------|-----------------|
| CPU | `docker stats` | > 90% sustained |
| Memory | `docker stats` | > 85% (especially in local mode with PyTorch) |
| Disk (SQLite + uploads) | `du -sh data/` | > 80% of volume |
| Docker container restarts | `docker inspect --format='{{.RestartCount}}'` | > 0 |

## Docker Health Check

The `docker-compose.yml` includes a built-in health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Docker will mark the container as `unhealthy` after 3 consecutive failures.

## Log Monitoring

### Backend logs (uvicorn)

```bash
docker compose logs -f backend
```

Watch for:
- `ERROR` or `CRITICAL` log levels
- `TimeoutError` from Docling processing
- `sqlite3.OperationalError` (DB issues)
- `429 Too Many Requests` spikes

### Frontend logs (nginx)

```bash
docker compose logs -f frontend
```

Watch for:
- `502 Bad Gateway` (backend down)
- `413 Request Entity Too Large` (file size limit)

## Recommended Setup

For production deployments, consider:

1. **Uptime monitor** — ping `/api/health` every 60s (UptimeRobot, Healthchecks.io)
2. **Log aggregation** — ship Docker logs to a central service
3. **Alerting** — notify on container restart, health check failure, or error spike
