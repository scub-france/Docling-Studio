# Changelog

All notable changes to Docling Studio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.1] - 2026-04-30

### Fixed

- Nginx upload body cap raised from 5 MB to 200 MB (`NGINX_MAX_BODY_SIZE`, default `200M`); uploads larger than 5 MB no longer returned 413 before reaching the backend.

## [0.5.0] - 2026-04-28

### Added

- Reasoning-trace viewer: SQLite-backed graph built from `document_json`, iteration-by-iteration overlay on the document outline (StructureViewer + GraphView), bidirectional PDF ↔ graph focus
- Live reasoning runner via [docling-agent](https://github.com/docling-project/docling-agent) (Ollama backend): `POST /api/documents/:id/reasoning` returns answer + iteration trace + convergence flag (gated by `REASONING_ENABLED`, off by default)
- `LLMProvider` port abstraction with `OllamaProvider` adapter — opens the door to alternate LLM backends once docling-agent supports them
- Neo4j graph storage pipeline: `TreeWriter` + `ChunkWriter` adapters, schema bootstrap, graph fetch endpoint, `Maintain` step with cytoscape-based graph visualization
- Architecture decision record (ADR-001): graph visualization library choice and 200-page endpoint cap
- Remote chunking: enabled in Docling Serve mode (previously local-only)
- Hexagonal architecture tests powered by `pytestarch` (CI-enforced)
- Centralized magic numbers for page dimensions, limits, and timeouts
- Paste image size/type limits (env vars `MAX_PASTE_IMAGE_SIZE_MB`, `PASTE_ALLOWED_IMAGE_TYPES`); surfaced in `/api/health`

### Changed

- **Breaking — `RAG_*` env vars renamed to `REASONING_*`**: `RAG_ENABLED` → `REASONING_ENABLED`, `RAG_MODEL_ID` → `REASONING_MODEL_ID`. Health response field `ragAvailable` → `reasoningAvailable`. New `LLM_PROVIDER_TYPE` env var (default `ollama`) materializes the LLM-provider abstraction.
- **Breaking — reasoning endpoint renamed `/rag` → `/reasoning`**: `POST /api/documents/:id/rag` is now `POST /api/documents/:id/reasoning`. Aligns with frontend `reasoning` feature naming.
- `api/reasoning.py` refactored to depend on `ReasoningRunnerPort`; concrete `docling-agent` integration moved to `infra/docling_agent_reasoning.py` (clean architecture)
- Frontend `reasoning` feature flag now reads `reasoningAvailable` from `/api/health`; sidebar entry hides when the backend is not wired (instead of failing with 503 on click)
- Documented that `docker-compose.yml` ships dev-only defaults (Neo4j `changeme` password, OpenSearch `DISABLE_SECURITY_PLUGIN=true`); operators must harden their own production deployments
- Backend logs a loud warning at boot if Neo4j is wired (`NEO4J_URI` set) with the default `changeme` password, so prod operators can't silently inherit it
- `DocumentConverter` port exposes `supports_page_batching: bool` so the analysis service no longer relies on `isinstance(converter, ServeConverter)` (LSP fix)
- `VectorStore` port gains a `ping()` method; `IngestionService.ping()` now goes through the port instead of reaching into `_vector_store._client` (encapsulation)
- API path parameters renamed `{job_id}` → `{analysis_id}` across `api/analyses.py` and `api/ingestion.py` to align the OpenAPI surface with the user-facing terminology (URL paths unchanged)
- Centralised `localStorage` keys (`docling-theme`, `docling-locale`) into `frontend/src/shared/storage/keys.ts` (`STORAGE_KEYS`)
- Removed the dead `apiUrl` ref from the settings store and its orphan `settings.apiUrl` i18n entries
- Document-status string `"uploaded"` extracted to `DOCUMENT_STATUS_UPLOADED` in `api/schemas.py`
- PDF preview endpoint (`GET /api/documents/{id}/preview`) now offloads the synchronous file read + rasterisation to a worker thread (`asyncio.to_thread`), unblocking the FastAPI event loop

### Fixed

- Graph: collapse Docling `InlineGroup` and `Picture` children to avoid empty leaf nodes (#197)
- Neo4j: rewrite `fetch_graph` using `CALL` subqueries for proper relationship traversal
- CI: install `pytestarch` in backend tests job (#177)
- CI: ignore CVE-2026-40393 (Mesa) with expiry — Debian has no backport (#190)
- Reasoning: re-scroll PDF when re-clicking the active iteration
- `infra/docling_tree.py:101` migrated `isinstance(bbox, (list, tuple))` to PEP 604 union (Ruff UP038)
- Cross-feature integration test moved out of `features/history/` into `src/__tests__/integration/` so feature folders stay self-contained
- Tightened terminal `assert X is not None` checks in domain/repo/service tests to compare the value (e.g. `isinstance(.., datetime)` after `mark_running()`/`mark_completed()`)

## [0.4.0] - 2026-04-13

### Added

- Inline chunk text editing: double-click or edit button to modify chunk text, with save/cancel and "modified" badge
- Docker Compose dev stack (`docker-compose.dev.yml`) with OpenSearch, Dashboards, hot-reload backend and Vite frontend
- Soft-delete chunks: delete button with confirmation dialog, chunks hidden from UI but preserved in data
- Vector index metadata schema: `IndexedChunk` domain model, OpenSearch mapping builder, configurable embedding dimension
- `VectorStore` port (Protocol): `ensure_index`, `index_chunks`, `search_similar`, `get_chunks`, `delete_document`
- OpenSearch adapter (`OpenSearchStore`): kNN vector search, full-text search, bulk indexing, document CRUD
- Embedding microservice (`embedding-service/`): sentence-transformers REST API with batch processing and Dockerfile
- `EmbeddingService` port and `EmbeddingClient` HTTP adapter for remote embedding generation
- Orchestrated ingestion pipeline: Docling → chunking → embedding → OpenSearch indexing (idempotent)
- Ingestion REST API: `POST /api/ingestion/{jobId}`, `DELETE /api/ingestion/{docId}`, `GET /api/ingestion/status`
- Production docker-compose with OpenSearch and embedding service
- E2E Karate test for full ingestion workflow (PDF → chunks in OpenSearch)
- My Documents screen: search, filter (all/indexed/not indexed), sort (name/date), ingestion status badges
- Ingest button in Studio: one-click ingestion from completed analysis with progress feedback

### Fixed

### Changed

## [0.3.1] - 2026-04-09

### Added

- Batch conversion progress: segmented progress bar with ring indicator and per-batch visual feedback
- Inline mini progress bar in the top banner during analysis
- Informational notice in Prepare mode when chunking is unavailable (batch mode)
- `BATCH_PAGE_SIZE` environment variable forwarded in Docker Compose

### Fixed

- Batch progress reset to null on completion (progress_current/progress_total overwritten by stale in-memory job object)
- Regression test for batch progress preservation in `_run_analysis_inner` flow
- E2E assertion on final progress values in batch-progress feature

## [0.3.0] - 2026-04-07

### Added

- Chunking support: domain objects, persistence, API endpoints, and frontend Prepare mode
- Chunk-to-bbox hover highlighting in Prepare mode
- Page filtering and collapsible config in Prepare mode
- Feature flipping mechanism
- Reusable pagination composable and PaginationBar component
- Version display in sidebar, settings page, and health endpoint

### Fixed

- Feature flag health check blocked by CORS
- Zombie jobs and unprotected JSON parse
- Upload error not displayed in DocumentUpload component
- Serve API contract: send `to_formats` as repeated form fields
- Audit findings: security, robustness, dead code, domain-infra violation

### Changed

- Refactored backend to hexagonal architecture for converter extensibility
- Added ServeConverter adapter for remote Docling Serve integration
- Moved `@vitest/mocker` from dependencies to devDependencies

## [0.2.0] - 2025-05-14

### Added

- Multi-arch Docker image release pipeline (GitHub Actions)
- Docker image published to `ghcr.io/scub-france/Docling-Studio`

## [0.1.0] - 2025-01-01

### Added

- Initial release of Docling Studio
- PDF upload and document management
- Configurable Docling pipeline (OCR, tables, code, formulas, images)
- Bounding box visualization with color-coded overlays
- Per-page results synchronized with PDF viewer
- Markdown and HTML export
- Analysis history with re-visit capability
- Dark/Light theme support
- French and English localization
- Docker and Docker Compose deployment
- CI/CD with GitHub Actions (tests + multi-arch Docker build)
- Health check endpoint (`/health`)
- SQLite-backed persistence
