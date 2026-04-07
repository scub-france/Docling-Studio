# Architecture

## Overview

![Docling Studio architecture](images/global.png){ width="700" }

Two services communicating via REST. The frontend is a Vue 3 SPA served by Nginx in production. The backend is a FastAPI app that wraps Docling's document conversion engine.

### Zooming into the backend

The schema above shows the macro view. Inside the backend, the code follows a **Clean Architecture** with strict layer boundaries:

```
┌──────────────────────────────────────────────────────┐
│                     Backend                           │
│                                                      │
│   ┌──────────┐                                       │
│   │   api/   │  ← HTTP (FastAPI routes, Pydantic)    │
│   └────┬─────┘                                       │
│        │ calls                                       │
│   ┌────▼─────┐                                       │
│   │services/ │  ← Use case orchestration             │
│   └──┬────┬──┘                                       │
│      │    │                                          │
│  ┌───▼──┐ ┌▼───────────┐                             │
│  │domain│ │persistence/ │                             │
│  │      │ │             │                             │
│  │bbox  │ │ SQLite CRUD │  ← Storage (your blue box) │
│  │parse │ │ file store  │                             │
│  └──────┘ └─────────────┘                             │
│  ↑ pure Python, no deps   ↑ aiosqlite               │
└──────────────────────────────────────────────────────┘
```

Dependencies flow **inward**: `api → services → domain`. The domain layer has zero knowledge of HTTP or database.

## Backend — Clean Architecture

The backend follows a strict layered architecture. Dependencies flow inward: API → Services → Domain. The domain layer has zero knowledge of HTTP or database.

```
document-parser/
├── main.py                   # FastAPI app, CORS, lifespan, health endpoint
│
├── domain/                   # Pure domain — no HTTP, no DB
│   ├── models.py             # Document, AnalysisJob dataclasses
│   ├── ports.py              # Abstract protocols (DocumentConverter, DocumentChunker)
│   ├── value_objects.py      # ConversionResult, ChunkingOptions, ChunkResult
│   └── bbox.py               # Bounding box coordinate normalization
│
├── api/                      # HTTP layer (FastAPI routers)
│   ├── schemas.py            # Pydantic DTOs (camelCase serialization)
│   ├── documents.py          # /api/documents endpoints
│   └── analyses.py           # /api/analyses endpoints (create, rechunk, delete)
│
├── persistence/              # Data layer (SQLite via aiosqlite)
│   ├── database.py           # Connection management, schema init
│   ├── document_repo.py      # Document CRUD
│   └── analysis_repo.py      # AnalysisJob CRUD
│
├── infra/                    # Infrastructure adapters
│   ├── settings.py           # Environment-based configuration
│   ├── local_converter.py    # In-process Docling converter (local mode)
│   ├── serve_converter.py    # HTTP client for Docling Serve (remote mode)
│   ├── local_chunker.py      # In-process chunking (HierarchicalChunker, HybridChunker)
│   ├── rate_limiter.py       # Sliding-window rate limiting middleware
│   └── bbox.py               # Bbox coordinate normalization helpers
│
├── services/                 # Use case orchestration
│   ├── document_service.py   # Upload, delete, preview
│   └── analysis_service.py   # Async Docling processing + chunking
│
└── tests/                    # pytest (199 tests)
```

### Layer responsibilities

| Layer | Role | Depends on |
|-------|------|------------|
| **domain** | Dataclasses, value objects, abstract ports | Nothing (pure Python) |
| **persistence** | SQLite CRUD, aiosqlite | domain (models) |
| **infra** | Adapters: converters, chunker, rate limiter, settings | domain (ports, value objects) |
| **services** | Orchestrate use cases, call converters/chunkers | domain + persistence + infra |
| **api** | HTTP endpoints, Pydantic DTOs, error handling | services |

### API contract

The API uses **camelCase** serialization (via Pydantic `alias_generator`), while the backend uses **snake_case** internally. The `pages_json` field contains raw `dataclasses.asdict()` output, so page data uses **snake_case** (`page_number`, not `pageNumber`).

## Frontend — Feature-Based

The frontend is organized by feature, each with its own store, API client, and UI components.

```
frontend/src/
├── app/                      # App shell, router, global styles
├── pages/                    # Route-level pages
│   ├── HomePage.vue
│   ├── StudioPage.vue        # PDF viewer + config + results
│   ├── DocumentsPage.vue
│   ├── HistoryPage.vue
│   └── SettingsPage.vue
│
├── features/                 # Feature modules
│   ├── analysis/             # Analysis store, API, bbox scaling, UI
│   │   ├── store.ts
│   │   ├── api.ts
│   │   ├── bboxScaling.ts    # Pure math: page coords → pixel coords
│   │   └── ui/
│   │       ├── BboxOverlay.vue
│   │       ├── AnalysisPanel.vue
│   │       ├── StructureViewer.vue
│   │       └── ...
│   ├── chunking/             # Chunk panel UI + rechunk action
│   ├── document/             # Document store, API, upload
│   ├── feature-flags/        # Feature flag store (reads /api/health)
│   ├── history/              # History store, navigation
│   └── settings/             # Theme, locale, API URL
│
└── shared/                   # Cross-feature utilities
    ├── types.ts              # All shared TypeScript interfaces
    ├── i18n.ts               # FR/EN translations
    ├── format.ts             # Date/size formatters
    └── api/http.ts           # HTTP client (fetch wrapper)
```

### Data flow

```
User action → Pinia store action → API client (fetch) → Backend REST endpoint
                                                              │
Backend response → Pinia store state → Vue reactivity → UI update
```

### Key design decisions

- **Pinia stores** per feature, not global. Each feature owns its state.
- **TypeScript strict mode** with shared interfaces in `shared/types.ts`.
- **No component library** — custom CSS with CSS variables for theming.
- **vue-tsc** in CI to catch type errors before merge.

## Feature Flags

The frontend adapts its UI based on the backend's capabilities. On startup, the feature flag store fetches `/api/health` and reads the `engine` and `deploymentMode` fields.

| Flag | Condition | Effect |
|------|-----------|--------|
| `chunking` | `engine === 'local'` | Shows chunking options in the analysis panel |
| `disclaimer` | `deploymentMode === 'huggingface'` | Shows a disclaimer banner at the top of the app |

This allows the same frontend build to work with both local and remote backends without conditional compilation.

## Rate Limiting

The backend applies a sliding-window rate limiter as middleware:

- **60 requests** per **60 seconds** per client IP
- The `/api/health` endpoint is excluded
- When the limit is exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header

## Analysis Lifecycle

An analysis job follows this state machine:

```
PENDING → RUNNING → COMPLETED
                  → FAILED
```

| Status | Description |
|--------|-------------|
| `PENDING` | Job created, waiting for a processing slot |
| `RUNNING` | Docling conversion in progress |
| `COMPLETED` | Conversion finished — results available (markdown, HTML, pages, chunks) |
| `FAILED` | Conversion error — `error_message` contains details |

The backend limits parallel jobs via `MAX_CONCURRENT_ANALYSES` (default: 3) to avoid overloading the CPU during Docling processing.

## Local vs Remote Mode

The backend supports two conversion engines, selected via the `CONVERSION_ENGINE` environment variable:

| | Local | Remote |
|---|---|---|
| **Engine** | In-process Docling (PyTorch) | HTTP client to [Docling Serve](https://github.com/DS4SD/docling-serve) |
| **Chunking** | Available (in-process) | Not available |
| **Docker image** | `latest-local` (~1.9 GB) | `latest-remote` (~270 MB) |
| **ML models** | Downloaded on first run (~400 MB) | Managed by Docling Serve |
| **CPU/RAM** | 4+ CPUs, 6+ GB RAM | 2 CPUs, 2 GB RAM |

The converter is selected at startup in `main.py` via `_build_converter()`. The chunker (`_build_chunker()`) is only instantiated in local mode — in remote mode, the chunking feature flag is disabled and the UI hides the chunking panel.

## Health Endpoint

`GET /api/health` returns the backend status:

```json
{
  "status": "ok",
  "engine": "local",
  "version": "0.3.0",
  "deploymentMode": "self-hosted"
}
```

The frontend uses this response to:

1. Verify the backend is reachable
2. Evaluate feature flags (chunking, disclaimer)
3. Display the app version
