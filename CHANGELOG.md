# Changelog

All notable changes to Docling Studio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
