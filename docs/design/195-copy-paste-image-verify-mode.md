# Design: Copy paste image in Verify mode

<!--
Design doc template for Docling Studio.

One design doc per tracked issue. File path convention:
  docs/design/<issue-number>-<kebab-slug>.md

Status lifecycle: Draft → In review → Accepted → Implemented (or Superseded).
Bump the Status line as the doc progresses; do not delete sections on the way.

This template is tailored to the project's architecture and conventions:
  - Backend Hexagonal Architecture / ports & adapters
    (domain → api/services/persistence/infra)
    see docs/architecture.md
  - Backend coding standards (FastAPI + Pydantic camelCase, aiosqlite,
    Python snake_case internal, max 300 lines/file, 30 lines/function)
    see docs/architecture/coding-standards.md
  - Frontend feature-based organization (Vue 3 + Pinia, one store per
    feature, Composition API, TypeScript strict, data-e2e selectors)
  - E2E with Karate UI (NOT Playwright) — see e2e/CONVENTIONS.md
  - Audit dimensions used at release gate — see docs/audit/master.md
  - ADR process for load-bearing decisions — see docs/architecture/adr-guide.md

The `/conception` command pre-fills the header block and §1 / §2 / §12 from
the linked issue. Everything else is on the author.
-->

- **Issue:** #195
- **Title on issue:** [ENHANCEMENT] Copy paste image in Verify mode
- **Author:** Pier-Jean Malandrino
- **Date:** 2026-04-23
- **Status:** Accepted
- **Target milestone:** 0.5.0
- **Impacted layers:** <backend: domain | api | services | persistence | infra> · <frontend: features/<name> | shared | app> · <e2e> · <infra/CI>
- **Audit dimensions likely touched:** <pick from: Hexagonal Architecture · DDD · Clean Code · KISS · DRY · SOLID · Decoupling · Security · Tests · CI/Build · Documentation · Performance>
- **ADR spawned?:** <no>  *(write an ADR when choosing a library, moving a boundary, or deciding **not** to do something — see `docs/architecture/adr-guide.md`)*

---

## 1. Problem

<!--
What hurts today, and for whom. Pull from the issue's Context + Current
behavior sections — keep the user's voice, do not paraphrase aggressively.
Two or three short paragraphs is usually enough. If you can't state the
problem in plain language, you are not ready to design a solution.
-->

TODO: Why this issue exists. Link the user story, incident, or upstream discussion that motivates it.

Today in Verify mode regarding image handling: TODO — describe the current baseline (upload-only? no paste target? no drag-drop?).

## 2. Goals

<!--
Concrete, verifiable outcomes. Convert the issue's acceptance criteria into
checkboxes here; the design is "done" when all are satisfied. Keep the list
small — five or fewer goals is a good smell.
-->

Users should be able to copy/paste images directly into Verify mode (e.g. from clipboard) instead of only via file upload.

- [ ] Define paste source (OS clipboard, drag-drop, screenshot)
- [ ] Define target area in Verify mode UI
- [ ] Define supported image formats and size limits
- [ ] Size / type limits are env-var configurable, carry sane defaults, and are documented in `README.md` + `docs/deployment/*` (e.g. `MAX_PASTE_IMAGE_SIZE_MB`, `PASTE_ALLOWED_IMAGE_TYPES`)

## 3. Non-goals

<!--
What this design explicitly does NOT try to solve — and, for each, where it
*should* be solved (follow-up issue, next milestone, different audit area).
This is the section that saves the review: naming the off-ramps up front
prevents scope creep. If you leave this empty, reviewers will fill it in
for you, badly.
-->

- ...
- ...

## 4. Context & constraints

<!--
The surrounding reality the design has to live in.

### Existing code surface
List the modules / files / stores this change touches. Prefer concrete paths
over prose:
  - Backend: document-parser/<layer>/<file>.py
  - Frontend: frontend/src/features/<name>/{store,api,ui}.ts|.vue
  - Persistence: document-parser/persistence/<repo>.py + schema in database.py
  - E2E: e2e/<feature>.feature

### Hexagonal Architecture constraints (backend)
The domain layer has zero imports from api / persistence / infra, and
defines ports (abstract protocols) that `infra/` adapters implement.
Persistence imports only from domain. API never imports persistence
directly — it goes through services. Call out any change that crosses
these lines or adds / moves a port.

### Deployment modes
Docling Studio ships two images (`latest-local`, `latest-remote`) driven by
`CONVERSION_ENGINE` — and a HF Space deployment on top of `latest-remote`.
State which modes this design supports, which it does not, and how the
frontend's feature flags (`chunking`, `disclaimer`) are affected.

### Hard constraints
Compatibility (SQLite schema, API contract, Pydantic DTOs), deadlines
(milestone due date), deployment target (Docker Compose, HF Space),
performance budget (matters for Performance audit), license / privacy
(matters for Security audit).
-->

### SQLite & storage limits (must be enforced upstream of the DB)

Pasted images follow the existing `documents` pattern: bytes land on disk
under `UPLOAD_DIR`, the row stores `storage_path: TEXT`. We do **not**
store base64 or BLOBs. Even so, app-level size guards must stay below
SQLite's structural limits so a malformed request can never wedge the
engine.

Relevant SQLite defaults (see https://www.sqlite.org/limits.html):

| SQLite limit | Default | Relevance |
|---|---|---|
| `SQLITE_MAX_LENGTH` | 1 GB (1 × 10⁹ bytes) | Max size of any single `TEXT` / `BLOB` cell. Irrelevant as long as we keep bytes off the DB. |
| `SQLITE_MAX_SQL_LENGTH` | 1 MB | Max length of an SQL statement incl. inlined literals. Always use parameter binding — never inline image bytes. |
| Page cache / WAL growth | n/a | Large writes bloat WAL until checkpoint; another reason to stay off-DB. |

Our own app-level limits guard against ever reaching those ceilings.
All such limits **must**: (1) carry a sane default in `infra/settings.py`,
(2) be overridable via env var, (3) be documented in `README.md` and
`docs/deployment/*`. This is consistent with how `MAX_FILE_SIZE_MB`
(default 50) is handled today.

## 5. Proposed design

<!--
The recommended approach, in enough detail that a competent engineer
outside the immediate context can implement it. Describe contracts, not
code — the PR is where code lives.

Structure this section by layer. Skip a layer if it is genuinely untouched;
do not pad.

### 5.1 Domain
New or changed dataclasses / value objects / ports in `document-parser/domain/`.
No HTTP or DB concerns here. If you are adding a port (`Protocol`), give its
full signature.

### 5.2 Persistence
Schema changes (table, columns, indexes), migration plan, aiosqlite query
shape. Note whether existing rows need a backfill.

### 5.3 Infra adapters
New or changed adapters in `document-parser/infra/` (converter, chunker,
rate limiter, settings). For new env vars, give name / default / allowed
values.

### 5.4 Services
Use-case orchestration in `document-parser/services/`. Services do NOT
implement — they delegate. Describe the call sequence, error handling,
and concurrency (how does this interact with `MAX_CONCURRENT_ANALYSES`?).

### 5.5 API
Endpoint additions / changes in `document-parser/api/`. For each:
  - Method + path
  - Request DTO (Pydantic, camelCase via alias_generator)
  - Response DTO (camelCase; remember `pages_json` stays snake_case)
  - Error responses (status codes, shape)
  - Whether it is excluded from the rate limiter (like `/api/health`)

### 5.6 Frontend — feature module
Which `frontend/src/features/<name>/` folder, which Pinia store actions,
which API client calls in `api.ts`, which Vue components in `ui/`. Name
new `data-e2e` attributes here (Karate needs them).

### 5.7 Cross-cutting
Feature flags (how the backend advertises capability via `/api/health` and
how the frontend reacts), i18n strings (`shared/i18n.ts`), shared types
(`shared/types.ts`).

Prefer mermaid / ASCII for sequence and data flow. Interfaces are more
valuable than pseudocode.
-->

### 5.1 Domain

### 5.2 Persistence

### 5.3 Infra adapters

Extend `document-parser/infra/settings.py` with paste-specific limits.
Follow the existing `MAX_FILE_SIZE_MB` pattern: typed field on the
settings dataclass, `os.environ.get(...)` with a string default, cast
at load time.

| Setting | Env var | Default | Allowed | Notes |
|---|---|---|---|---|
| `max_paste_image_size_mb` | `MAX_PASTE_IMAGE_SIZE_MB` | `10` | positive int, `0` = unlimited | Must be ≤ `MAX_FILE_SIZE_MB`; upload validator rejects larger payloads before any DB write. |
| `paste_allowed_image_types` | `PASTE_ALLOWED_IMAGE_TYPES` | `image/png,image/jpeg,image/webp` | comma-separated MIME list | Enforced server-side; frontend uses the same list via `/api/health`. |

Validation happens in the API layer (upload handler) **before** the
bytes reach persistence. Any future move to BLOB storage would still
rely on these guards — they are the contract that prevents us ever
approaching `SQLITE_MAX_LENGTH`.

### 5.4 Services

### 5.5 API

### 5.6 Frontend — feature module

### 5.7 Cross-cutting (feature flags, i18n, shared types)

## 6. Alternatives considered

<!--
At least two genuine alternatives, each with a one-paragraph description
and the reason it was rejected. "Do nothing" is often a legitimate
alternative — name it if it is. Reviewers use this section to sanity-check
that the recommended design was a choice and not the first thing that
came to mind.

If one of the alternatives represents a significant architectural fork
(e.g. introducing a new service, replacing a library), spawn an ADR under
`docs/architecture/adrs/` and link it in §12 — the design doc captures the
local decision, the ADR captures the cross-cutting one.
-->

### Alternative A — <name>

- **Summary:**
- **Why not:**

### Alternative B — <name>

- **Summary:**
- **Why not:**

## 7. API & data contract

<!--
Make the wire contract explicit — this is what the frontend, e2e tests,
and any external consumer will code against.

### Endpoints
| Method | Path | Request | Response | Breaking? |
|--------|------|---------|----------|-----------|
|        |      |         |          |           |

Remember:
  - API serialization is camelCase (Pydantic `alias_generator`).
  - Backend internals stay snake_case.
  - `pages_json` is the documented exception — it carries raw
    `dataclasses.asdict()` output (snake_case).
  - Health endpoint (`/api/health`) may need new fields if this design adds
    a feature flag.

### Persistence schema
```sql
-- ALTER TABLE / CREATE TABLE statements, with reasoning
```

### Env vars / config

All new knobs must land in `README.md` and `docs/deployment/*` (same
tables that already list `MAX_FILE_SIZE_MB`, `UPLOAD_DIR`, etc.).

| Name | Default | Allowed | Notes |
|------|---------|---------|-------|
| `MAX_PASTE_IMAGE_SIZE_MB` | `10` | positive int (`0` = unlimited) | Guards app-level payload size; must stay ≤ `MAX_FILE_SIZE_MB` to avoid double-gating confusion. |
| `PASTE_ALLOWED_IMAGE_TYPES` | `image/png,image/jpeg,image/webp` | comma-separated MIME list | Surfaced to the frontend via `/api/health` so the paste handler can reject client-side. |

SQLite ceilings (`SQLITE_MAX_LENGTH` = 1 GB, `SQLITE_MAX_SQL_LENGTH` =
1 MB) are **not** env-configurable — they are compile-time properties
of the bundled engine. Document them in `docs/deployment/*` as
background so operators understand why the app-level limits exist.

### Breaking changes
Enumerate anything a consumer must change. If there are none, say so
explicitly — "additive only" is a useful commitment.
-->

## 8. Risks & mitigations

<!--
One row per non-trivial risk. Map each to an audit dimension so the
release-gate audit has a clear hook:

| Risk | Audit dimension | Likelihood | Impact | How we notice | Mitigation / rollback |
|------|-----------------|-----------|--------|---------------|------------------------|
|      | Security        |           |        |               |                        |
|      | Performance     |           |        |               |                        |
|      | Decoupling      |           |        |               |                        |

Common families to scan for:
  - **Hexagonal Architecture:** cross-layer imports, leaking HTTP into domain, adapter bypassing its port
  - **Security:** rate limiter bypass, path traversal on uploads, SSRF via
    the remote converter, unauthenticated data exposure
  - **Performance:** synchronous work on the FastAPI event loop,
    unbounded queries, new work inside `MAX_CONCURRENT_ANALYSES` budget
  - **Tests:** coverage gap on a critical path
  - **Documentation:** missing README / env var / i18n entry

A design with "no risks identified" is a design that has not been read
carefully.
-->

| Risk | Audit dimension | Likelihood | Impact | How we notice | Mitigation / rollback |
|------|-----------------|------------|--------|---------------|------------------------|
|      |                 |            |        |               |                        |

## 9. Testing strategy

<!--
How this design will be verified. Be specific — name files / suites.

### Backend — pytest (`document-parser/tests/`)
  - Unit: per-layer (`tests/domain/`, `tests/persistence/`, `tests/services/`)
  - Integration: services wired with real aiosqlite + real adapters
  - Architecture tests (if applicable): enforce import boundaries

### Frontend — Vitest (`frontend/src/**/*.test.ts`)
  - Stores: actions / getters / mocked API
  - Pure helpers (e.g. `bboxScaling.ts`-style modules): deterministic
  - Components only when behavior is non-trivial; do not test markup

### E2E — Karate UI (`e2e/`)
  - Use `data-e2e` selectors — never CSS classes (see e2e/CONVENTIONS.md)
  - `retry()` / `waitFor()` — never `Thread.sleep()` / `delay()`
  - Setup via API, verify via UI, cleanup via API
  - Tag appropriately: `@critical` / `@ui` / `@smoke` / `@regression` / `@e2e`
  - **Never Playwright** — Karate is the tool here.

### Manual QA
Steps the reviewer can run locally (`docker-compose.dev.yml` up, scenario
to reproduce). Keep it short — if the manual list is long, automate more.

### Performance / load
Required when the design claims a latency / throughput / memory property,
or touches the conversion hot path.
-->

## 10. Rollout & observability

<!--
How this change gets to production safely.

### Release branch
Which `release/X.Y.Z` is the target? Any coordination with a parallel
release (e.g. R&D branch)?

### Feature flag / staged rollout
Does the change hide behind a flag surfaced via `/api/health`? If so, what
flips the flag, and what is the default? HF Space deployments often need
`deploymentMode === 'huggingface'` gating.

### Observability
  - Logs to add / extend (structured, low-cardinality keys)
  - Metrics / counters (if added — call out any new Prometheus names)
  - New error modes to watch for in `analysis_jobs.status = FAILED`

### Rollback plan
The revert that is safe to apply at any time:
  - Which migration is reversible? Which is not?
  - Which env var flip disables the feature without a redeploy?
  - Any data cleanup needed after rollback?

Link to the existing release / ops playbooks:
  - Deployment: `docs/release/*` (also surfaced via `/release:deploy`)
  - Rollback: also surfaced via `/release:rollback`
  - Incident: `docs/operations/*` (also surfaced via `/ops:incident`)
-->

## 11. Open questions

<!--
Things the author explicitly does not know yet, phrased as questions the
reviewer can answer or redirect. Empty is allowed once the design is
Accepted — during Draft / In review, this section is where the honest
uncertainty lives. Resolve or delete each entry before shipping.
-->

- ...
- ...

## 12. References

<!--
Links to everything a future reader would want.
-->

- **Issue:** https://github.com/scub-france/Docling-Studio/issues/195
- **Related PRs / commits:**
- **ADRs:** <ADR-NNN or "none planned">
- **Project docs:**
  - Architecture: `docs/architecture.md`
  - Coding standards: `docs/architecture/coding-standards.md`
  - ADR guide / template: `docs/architecture/adr-guide.md`, `docs/architecture/adr-template.md`
  - Audit master: `docs/audit/master.md`
  - E2E conventions: `e2e/CONVENTIONS.md`
- **External:** <specs, upstream issues, dashboards, third-party docs>
