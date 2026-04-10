# Stack Profile — FastAPI + Vue 3

Profile for running the 12 release audits on Docling Studio.

## Layer Mapping

| Generic Layer | Docling Studio Path | Language |
|---------------|---------------------|----------|
| **Domain** | `document-parser/domain/` | Python |
| **Services** | `document-parser/services/` | Python |
| **API** | `document-parser/api/` | Python |
| **Infrastructure** | `document-parser/infra/` | Python |
| **Persistence** | `document-parser/persistence/` | Python |
| **Frontend** | `frontend/src/` | TypeScript / Vue |
| **Tests (backend)** | `document-parser/tests/` | Python |
| **Tests (frontend)** | `frontend/src/**/*.test.*` | TypeScript |
| **Tests (e2e API)** | `e2e/api/` | Karate (Gherkin) |
| **Tests (e2e UI)** | `e2e/ui/` | Karate UI (Gherkin) |
| **CI/CD** | `.github/workflows/` | YAML |
| **Docker** | `Dockerfile`, `docker-compose.yml`, `nginx.conf` | Docker / Nginx |

## Excluded Paths

These paths are excluded from audits:

- `document-parser/.venv/`
- `document-parser/__pycache__/`
- `frontend/node_modules/`
- `frontend/dist/`
- `e2e/**/target/`

## Framework Detection

Imports that should NOT appear in the domain layer:

```python
# Forbidden in document-parser/domain/
from fastapi import ...
from pydantic import ...       # except BaseModel for value objects
import aiosqlite
from infra import ...
from persistence import ...
from api import ...
```

Imports that should NOT cross feature boundaries in the frontend:

```typescript
// features/analysis/ should NOT import from features/chunking/store
// features/document/ should NOT import from features/analysis/store
// Cross-feature communication goes through shared/ or events
```

## Tools & Commands

| Task | Command |
|------|---------|
| Backend lint | `cd document-parser && ruff check .` |
| Backend format | `cd document-parser && ruff format --check .` |
| Backend tests | `cd document-parser && pytest tests/ -v` |
| Frontend lint | `cd frontend && npx eslint src/` |
| Frontend type-check | `cd frontend && npm run type-check` |
| Frontend format | `cd frontend && npx prettier --check src/` |
| Frontend tests | `cd frontend && npm run test:run` |
| E2E API tests | `mvn test -f e2e/api/pom.xml -Dkarate.options="--tags @smoke"` |
| E2E UI tests | `mvn test -f e2e/ui/pom.xml -Dkarate.options="--tags @critical"` |
| Docker build | `docker compose build` |
| Docker health | `curl -s http://localhost:3000/api/health` |
| Dependency audit (Python) | `cd document-parser && pip audit` |
| Dependency audit (Node) | `cd frontend && npm audit` |
