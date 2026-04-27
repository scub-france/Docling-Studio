# Architecture Decision Records (ADR) — Guide

## What is an ADR?

An ADR is a short document that captures a significant architectural decision, along with the context and consequences. ADRs create a **decision log** so future contributors understand *why* the codebase looks the way it does.

## When to Write an ADR

Write an ADR when:

- Choosing or replacing a framework, library, or tool
- Changing the architecture (new layer, new pattern, new boundary)
- Making a trade-off that future developers might question
- Deciding NOT to do something (these are often the most valuable)

Do NOT write an ADR for:

- Implementation details that are obvious from the code
- Formatting or style choices (those go in [coding-standards.md](coding-standards.md))
- Bug fixes or minor refactors

## How to Write an ADR

1. Copy `adr-template.md` to `docs/architecture/adrs/ADR-NNN-short-title.md`
2. Number sequentially (ADR-001, ADR-002, ...)
3. Fill in all sections — especially **Context** (the *why*) and **Alternatives Considered**
4. Set status to `Proposed`
5. Open a PR for team review
6. Once merged, update status to `Accepted`

## Existing Decisions (captured retroactively)

These decisions were made before the ADR process was introduced. They are documented here for context:

| Decision | Rationale | Date |
|----------|-----------|------|
| Hexagonal Architecture (ports & adapters) for backend | Decouple domain from framework — enable converter swapping (local/remote) via ports | 2025-01 |
| FastAPI over Django | Async-first, lightweight, Pydantic-native — better fit for a single-purpose API | 2025-01 |
| Vue 3 + Pinia over React | Composition API + built-in reactivity — smaller bundle for this use case | 2025-01 |
| SQLite over PostgreSQL | Single-file DB, zero ops — appropriate for a document processing tool | 2025-01 |
| Karate over Playwright for e2e | Team expertise, unified API+UI testing, JVM ecosystem | 2026-03 |
| Feature flags via `/api/health` | No external service needed — backend capabilities drive frontend UI | 2026-03 |

## Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded by ADR-NNN]
```

- **Deprecated**: The decision is no longer relevant (feature removed, context changed)
- **Superseded**: A newer ADR replaces this one (link to the new ADR)
- Never delete an ADR — mark it as deprecated/superseded instead
