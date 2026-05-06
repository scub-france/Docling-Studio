# Design: Optim taille image latest-local (sortir reasoning, multi-stage, dockerignore)

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

- **Issue:** #254
- **Title on issue:** [ENHANCEMENT] Optim taille image latest-local (sortir reasoning, multi-stage, dockerignore)
- **Author:** Pier-Jean Malandrino
- **Date:** 2026-05-06
- **Status:** Implemented
- **Target milestone:** 0.6.0 — Doc-centric ingest
- **Impacted layers:** infra/CI (Dockerfile, requirements split, compose) · docs (README, this doc)
- **Audit dimensions likely touched:** CI/Build · Performance · Decoupling · Documentation
- **ADR spawned?:** no  *(no load-bearing library/boundary change — Docker layout choice is locally scoped)*

---

## 1. Problem

L'image `latest-local` empile aujourd'hui beaucoup de surface : `torch` + `torchvision` (CPU, ~800 Mo–1.2 Go), `docling>=2.80`, et — par effet de bord — `docling-agent` + `mellea` qui sont déclarés dans `requirements.txt` et donc tirés **aussi** par la cible `remote` (qui devrait être lightweight).

Le `Dockerfile` actuel souffre par ailleurs de plusieurs problèmes de build qui pénalisent la taille et le temps de rebuild : `COPY . .` se fait dans la stage `base`, donc toute modification de code Python invalide les layers `pip install` de la stage `local` (rebuild complet de torch à chaque commit) ; pas de stage builder isolée → pip + caches restent dans l'image finale ; `.dockerignore` minimal — pas d'exclusion de `tests/`, `data/`, `uploads/`, `docs/`, etc. ; reasoning (R&D, gated par `REASONING_ENABLED`) embarqué inconditionnellement dans toutes les images.

## 2. Goals

<!--
Concrete, verifiable outcomes. Convert the issue's acceptance criteria into
checkboxes here; the design is "done" when all are satisfied. Keep the list
small — five or fewer goals is a good smell.
-->

- [ ] Baseline mesurée et notée dans le design doc (`docker images` + `docker history` du top-3 layers).
- [ ] `docling-agent` + `mellea` retirés de `document-parser/requirements.txt`, déplacés dans `document-parser/requirements-reasoning.txt`.
- [ ] `Dockerfile` multi-stage (`builder` + cible finale) avec `COPY . .` repoussé après les `pip install`.
- [ ] Build-arg `WITH_REASONING=false` (défaut) supporté dans la cible `local`.
- [ ] `.dockerignore` étendu (`tests/`, `data/`, `uploads/`, `docs/`, `*.iml`, `package-lock.json`, `node_modules/`, `tools/migrate_06.py`).
- [ ] Évaluation de `torchvision` documentée (gardé ou retiré, justifié).
- [ ] Volume HF cache documenté dans `docker-compose.yml` et `docker-compose.dev.yml`.
- [ ] Smoke test : conversion locale OK sans reasoning ; reasoning OK avec `WITH_REASONING=true` + `REASONING_ENABLED=true` + Ollama joignable.
- [ ] `pytest tests/ -v` passe dans le container final.
- [ ] Réduction taille ≥ 30 % vs baseline (chiffrée dans la PR).

## 3. Non-goals

<!--
What this design explicitly does NOT try to solve — and, for each, where it
*should* be solved (follow-up issue, next milestone, different audit area).
This is the section that saves the review: naming the off-ramps up front
prevents scope creep. If you leave this empty, reviewers will fill it in
for you, badly.
-->

- **Pas de réécriture du `LocalConverter`** ni de suppression du `threading.Lock` global → suivi perf séparé (issue dédiée à ouvrir si besoin).
- **Pas de bake-in des modèles Docling** dans l'image — le compromis taille est trop défavorable. Le cache HF reste mountable via volume ; un `tools/prefetch_models.py` opt-in pourra arriver dans un autre issue.
- **Pas d'optim de l'image `embedding-service`** — autre image, autre périmètre.
- **Pas de tuning HF Space deploy** — HF Space déploie `latest-remote`, pas `latest-local`.
- **Pas de changement du moteur OCR** livré par Docling.
- **Pas de modification de l'API publique** ni du schéma SQLite — change additif/build-only.

## 4. Context & constraints

### Existing code surface

- `document-parser/Dockerfile` — the multi-target file (`base` → `remote` / `local`)
- `document-parser/requirements.txt` — shared deps for both targets
- `document-parser/requirements-local.txt` — additive Docling stack for the local target
- `document-parser/.dockerignore` — minimal exclusion list
- `docker-compose.yml` / `docker-compose.dev.yml` — both reference `target: ${CONVERSION_MODE:-local}`
- `document-parser/infra/docling_agent_reasoning.py` — already guards with `deps_present()`, so removing the deps from the standard image degrades gracefully

No domain / API / persistence / services code is touched. No SQLite migration. No frontend change. No e2e change.

### Hexagonal Architecture constraints

None crossed. The change lives entirely in `infra/CI` (Docker + requirements files). Domain/API/services/persistence are untouched and the `LocalConverter` / `ReasoningRunner` ports keep their existing shapes — only the deployment artefact changes shape, not the code.

### Deployment modes

- `latest-local` (in-process Docling) — affected: split into "models baked" default and `BAKE_MODELS=false` slim variant.
- `latest-remote` (delegates to Docling Serve) — affected: also slimmed (it inherited the reasoning deps via the shared `requirements.txt`).
- HF Space — uses `latest-remote`, so it gets the size win for free without any HF-specific change.
- Frontend feature flags (`chunking`, `disclaimer`, `reasoningAvailable`) are unaffected; `reasoningAvailable` keeps reflecting `deps_present()` so the sidebar entry hides automatically when the standard image is used.

### Hard constraints

- **No SQLite or API contract change** — additive build-only.
- **No Pydantic DTO change.**
- **Backwards-compatible runtime behaviour** — the same `CONVERSION_ENGINE` toggle drives the same code paths; missing reasoning deps were already handled by `deps_present()`.
- **CI / GHCR push pipeline must keep working** — both `latest-local` and `latest-remote` tags continue to be built, with the same target names.
- **Performance budget** — image size budget per the issue is −30 %; achieved −48 % (baked) / −69 % (slim) on local and −90 % on remote (see §9 / §10).

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

Untouched.

### 5.2 Persistence

Untouched.

### 5.3 Infra adapters

Untouched at the Python level. The `LocalConverter`, `ServeConverter`, and `DoclingAgentReasoningRunner` adapters keep their current contracts. The only infra change is at the **deployment** layer:

- `requirements.txt` no longer carries `docling-agent==0.1.0` and `mellea==0.4.2`. They move to a new `requirements-reasoning.txt` (opt-in).
- `Dockerfile` is rewritten as a multi-stage build:

```
                 python:3.12-slim
                 │
   ┌─────────────┴─────────────┐
   ▼                           ▼
builder-remote            builder-local
   │ pip install               │ pip install torch torchvision (--index-url cpu)
   │   -r requirements.txt     │ pip install -r requirements-local.txt
   │                           │ if WITH_REASONING: pip install -r requirements-reasoning.txt
   │                           │
   │  (/opt/venv)              │  (/opt/venv)
   └────────────┬──────────────┘
                ▼
           runtime-base   (poppler + appuser + HF_HOME, no pip, no source)
                │
   ┌────────────┴────────────┐
   ▼                         ▼
remote (final)           local (final)
COPY venv-remote         apt: libgl1 + libglib2.0-0
COPY .                   COPY venv-local
                         if BAKE_MODELS: docling-tools models download
                         COPY .
```

- Source (`COPY . /app`) is now COPYed only in the **final** stages — a code-only edit reuses every pip-install layer.
- Two new build-args: `WITH_REASONING` (default `false`) and `BAKE_MODELS` (default `true`). Both opt-out for `local-reasoning` / slim variants respectively.

### 5.4 Services

Untouched.

### 5.5 API

Untouched.

### 5.6 Frontend — feature module

Untouched.

### 5.7 Cross-cutting (feature flags, i18n, shared types)

- `/api/health` — no schema change. `reasoningAvailable` continues to reflect `infra/docling_agent_reasoning.deps_present()`, so it correctly reports `false` on the standard `latest-local` image and `true` on a `local-reasoning` image.
- `i18n` — no string change.
- `shared/types.ts` — no type change.

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

### Alternative A — Dedicated `local-reasoning` Dockerfile target (3rd stage)

- **Summary:** Add a third final target `FROM local AS local-reasoning` that runs `pip install -r requirements-reasoning.txt`. CI publishes `latest-local` and `latest-local-reasoning` separately.
- **Why not:** Doubles the CI surface for very little benefit, and the duplication of intent (build-arg vs target) confuses operators. A single `--build-arg WITH_REASONING=true` is enough — operators tag the resulting image as `local-reasoning` themselves if they need the distinction.

### Alternative B — Bake reasoning deps into the standard image, do nothing

- **Summary:** Keep `docling-agent` + `mellea` in `requirements.txt`, accept the 5+ GB image as the cost of "everything works out of the box".
- **Why not:** The standard `latest-remote` image (which delegates to Docling Serve and never reasons locally) was carrying ~5 GB of unrelated CUDA + LLM SDK weights. That alone disqualifies the do-nothing path.

### Alternative C — Bake the Docling models into a separate image and mount as a sidecar volume

- **Summary:** Build a tiny "models-only" image, mount it as a read-only volume on the backend container.
- **Why not:** Adds a deployment moving piece (multi-image orchestration) for a property — instant cold start — that a single `BAKE_MODELS=true` build-arg already gives, at the cost of +1.3 GB the operator can opt out of.

## 7. API & data contract

### Endpoints

No change. `/api/health` keeps the same shape; `reasoningAvailable` still derives from runtime import-checks.

### Persistence schema

No change.

### Env vars / config

No new runtime env vars. Two new **build-args** on the `local` Dockerfile target:

| Name | Default | Allowed | Notes |
|------|---------|---------|-------|
| `WITH_REASONING` | `false` | `true` / `false` | Bundle `docling-agent` + `mellea`. Opt in to build a `local-reasoning` image. Off keeps the standard image lean. |
| `BAKE_MODELS` | `true` | `true` / `false` | Pre-fetch Docling model checkpoints into the appuser HF cache. Off makes the image ~1.3 GB lighter at the cost of a one-time download on first conversion. |

Compose forwards `WITH_REASONING` from the host env (`WITH_REASONING=true docker compose up --build`).

### Breaking changes

**Additive only at the deployment level. Two operational expectations change** — both intentional:

1. Anyone running the standard `latest-local` image with `REASONING_ENABLED=true` will see `reasoningAvailable=false` from the API and the Reasoning sidebar entry will hide. To restore: rebuild with `--build-arg WITH_REASONING=true`. (Already documented in README.)
2. The previously-added `hf_cache` named volume in compose is removed. Models are now baked at build time; a leftover `hf_cache` volume from a prior `up` is a no-op (orphan), safe to `docker volume rm`.

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
| A future transitive dep silently re-pulls a CUDA torch and inflates the image again | Performance · CI/Build | Medium | High | CI image-size step regresses; `docker history` shows nvidia-* layers | Pin `torch` to a `+cpu` build in the requirements files; add a CI check that fails if `nvidia-` packages appear in the venv |
| Operators relying on R&D reasoning hit `reasoningAvailable=false` after upgrading | Documentation · Decoupling | Medium | Medium | User report or 503 from `/api/reasoning` (already gated) | README + design doc explicitly call out the `WITH_REASONING=true` path; existing `deps_present()` already degrades gracefully (no crash) |
| Baked models become stale relative to a future Docling version bump | CI/Build | Low | Low | Backend logs HF cache version mismatch; conversion still works (Docling re-downloads if needed) | Models are re-fetched at every image build; bumping `docling` in requirements-local.txt naturally produces a fresh-baked image |
| A user adds custom models at runtime and loses them on container restart | Decoupling | Low | Low | User reports lost custom models | Documented: `BAKE_MODELS=false` + add a custom volume mount on `/home/appuser/.cache/huggingface` if persistence is needed |
| Multi-stage `COPY --from=builder` increases initial build time on a cold cache | CI/Build | Low | Low | CI build duration | Cold builds are sequential by design; warm builds are dramatically faster (pip layers reused on every Python edit) — net positive |

## 9. Testing strategy

### Backend — pytest

No new tests added. The change is build-only and the existing 563-test suite is the regression net (services, persistence, API contract — none touched).

Validation pipeline run on the branch:

```
ruff check .          → All checks passed
ruff format --check . → 99 files OK
pytest tests/         → 563 passed, 13 skipped
```

(2 pre-existing collection errors — `pytestarch` missing in dev venv, `_encode_picture_b64` not exported — are unrelated to this branch's diff and tracked separately.)

### Frontend — Vitest

Untouched. Not run.

### E2E — Karate UI

Not in scope. The change does not affect any user-facing behaviour.

### Manual QA

1. `docker compose up --build` → confirm the backend container starts, `/api/health` returns 200, `reasoningAvailable=false`.
2. Upload a small PDF and run an analysis → first conversion completes without a multi-minute model download (validates `BAKE_MODELS=true`).
3. Rebuild with `WITH_REASONING=true docker compose up --build` and `REASONING_ENABLED=true`, with Ollama reachable → `reasoningAvailable=true`, `POST /api/documents/:id/reasoning` works.
4. Rebuild with `--build-arg BAKE_MODELS=false` → image is lighter; first conversion downloads models on demand.

### Performance / load — image size measurements

Measured on arm64, cold Docker cache:

| Variant                                | Before    | After     | Δ      |
|----------------------------------------|----------:|----------:|-------:|
| `latest-local` (models baked, default) | 6.09 GB   | 3.19 GB   | −48 %  |
| `latest-local` (`BAKE_MODELS=false`)   | 6.09 GB   | 1.89 GB   | −69 %  |
| `latest-remote`                        | 5.85 GB   | 585 MB    | −90 %  |

Build durations (cold cache): `after-remote` ≈ 49 s, `after-local` ≈ 1 m 46 s. Warm rebuild after a Python-only edit: sub-second (pip layers reused).

## 10. Rollout & observability

### Release branch

Targets `release/0.6.0`. No coordination needed with parallel branches — the change is isolated to build files.

### Feature flag / staged rollout

No runtime feature flag. The change is hidden behind two **build-time** flags:

- `BAKE_MODELS=true` (default) — produces the standard ~3.2 GB image.
- `WITH_REASONING=true` (opt-in) — produces a `local-reasoning` variant.

Operators can roll out by re-pulling `latest-local` from GHCR; no env flip needed.

HF Space deployments are unaffected by the `local`-side build-args (HF Space uses `latest-remote`).

### Observability

- No new logs, metrics, or error modes.
- Image size becomes a CI signal: a follow-up issue should add a step that prints the published image size to the workflow summary, so a future regression (e.g. a new dep silently re-pulling CUDA) is visible at PR review time.

### Rollback plan

Pure-revert. Re-deploying the previous tag (`v0.5.x`) restores the prior image. No data migration or env flip is involved. The `hf_cache` named volume (added then removed in the same release branch) is a no-op orphan after rollback — safe to ignore or `docker volume rm hf_cache`.

## 11. Open questions

Resolved during implementation. Two follow-ups deferred to dedicated issues:

- Drop `docling-core[chunking]` extra from `requirements.txt` to push `latest-remote` from 585 MB toward the historical ~270 MB. Needs verification that the `infra/local_chunker.py` path is local-only (it appears to be, but a check is warranted).
- Pin `torch` to a CPU build (`torch==X.Y.Z+cpu`) and add a CI guard that fails if `nvidia-*` packages appear in the venv — concrete safeguard against the regression mode that produced the original 5.6 GB bloat.

## 12. References

<!--
Links to everything a future reader would want.
-->

- **Issue:** https://github.com/scub-france/Docling-Studio/issues/254
- **Related PRs / commits:** https://github.com/scub-france/Docling-Studio/pull/255
- **ADRs:** none planned
- **Project docs:**
  - Architecture: `docs/architecture.md`
  - Coding standards: `docs/architecture/coding-standards.md`
  - ADR guide / template: `docs/architecture/adr-guide.md`, `docs/architecture/adr-template.md`
  - Audit master: `docs/audit/master.md`
  - E2E conventions: `e2e/CONVENTIONS.md`
- **External:**
  - Upstream `_rag_loop` public-API replacement: https://github.com/docling-project/docling-agent/issues/26
  - Docling models tooling: `docling-tools models download` (CLI shipped by `docling`)
