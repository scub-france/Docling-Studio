# Coding Standards

Conventions for writing consistent, readable code across the Docling Studio codebase.

## Python (Backend — `document-parser/`)

### Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **Ruff** | Linting + formatting | `ruff.toml` / `pyproject.toml` |
| **pytest** | Testing | `pytest.ini` / `pyproject.toml` |
| **mypy** (optional) | Type checking | — |

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `analysis_repo.py` |
| Classes | `PascalCase` | `AnalysisJob`, `DocumentConverter` |
| Functions / methods | `snake_case` | `create_analysis()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CONCURRENT_ANALYSES` |
| Private | `_leading_underscore` | `_build_converter()` |

### Style Rules

- Max function length: **30 lines** (soft limit — justify longer ones)
- Max file length: **300 lines** (split into modules if exceeded)
- Imports: standard library → third-party → local, separated by blank lines
- Type hints on all public functions
- Docstrings only on non-obvious public APIs (don't state the obvious)
- No `# type: ignore` without a comment explaining why

### Architecture Rules

- **Domain layer** (`domain/`): zero imports from `api/`, `persistence/`, `infra/`
- **Persistence layer** (`persistence/`): only imports from `domain/`
- **API layer** (`api/`): never imports from `persistence/` directly — goes through `services/`
- **Services** (`services/`): orchestrate, don't implement — delegate to domain and infra

## TypeScript / Vue (Frontend — `frontend/src/`)

### Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **ESLint** | Linting | `.eslintrc.*` |
| **Prettier** | Formatting | `.prettierrc` |
| **vue-tsc** | Type checking | `tsconfig.json` |
| **Vitest** | Testing | `vitest.config.ts` |

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Components | `PascalCase.vue` | `BboxOverlay.vue` |
| Composables | `useCamelCase.ts` | `usePagination.ts` |
| Stores | `camelCase.ts` | `analysisStore.ts` |
| Types / Interfaces | `PascalCase` | `AnalysisJob`, `BboxRect` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE` |
| CSS classes | `kebab-case` | `.bbox-overlay` |
| `data-e2e` attributes | `kebab-case` | `data-e2e="upload-zone"` |

### Style Rules

- **Composition API** only (`<script setup lang="ts">`) — no Options API
- One component per file
- Props defined with `defineProps<T>()` (type-based, not runtime)
- Emits defined with `defineEmits<T>()`
- Pinia stores: one per feature, in the feature directory
- No global state outside Pinia
- API calls only in `api.ts` files (never in components or stores directly)

### API Contract

- Frontend sends/receives **camelCase** (Pydantic `alias_generator`)
- Backend uses **snake_case** internally
- `pages_json` is an exception — contains raw snake_case from `dataclasses.asdict()`

## Karate (E2E — `e2e/`)

See [e2e/CONVENTIONS.md](../../e2e/CONVENTIONS.md) for detailed rules.

Key points:
- Use `data-e2e` selectors, never CSS classes
- Use `retry()`/`waitFor()`, never `Thread.sleep()` or `delay()`
- Setup via API, verify via UI, cleanup via API
- Tag tests: `@critical`, `@ui`, `@smoke`, `@regression`, `@e2e`
