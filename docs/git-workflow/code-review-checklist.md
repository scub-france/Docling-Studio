# Code Review Checklist

Use this checklist when reviewing a Pull Request. Not every item applies to every PR — skip what is irrelevant, but consciously skip it rather than miss it.

## Correctness

- [ ] The code does what the PR description says it does
- [ ] Edge cases are handled (empty input, missing data, concurrent access)
- [ ] Error paths return meaningful messages, not stack traces
- [ ] No regressions on existing behavior

## Architecture & Design

- [ ] Dependencies flow inward: `api → services → domain` (never reversed)
- [ ] Domain layer has no imports from `api/`, `persistence/`, `infra/`
- [ ] No business logic in API routes — delegated to services
- [ ] New abstractions are justified (no premature generalization)
- [ ] Pinia stores stay within their feature boundary

## Security

- [ ] User input is validated at the API boundary (Pydantic schemas)
- [ ] No secrets, API keys, or credentials in the code
- [ ] No `eval()`, `exec()`, or raw SQL
- [ ] File paths are sanitized (no path traversal)
- [ ] CORS configuration is unchanged or explicitly justified

## Tests

- [ ] New behavior has corresponding tests
- [ ] Tests are deterministic (no `sleep`, no random, no network)
- [ ] Test names describe the scenario, not the implementation
- [ ] E2E tests use `data-e2e` attributes, not CSS classes (see [e2e/CONVENTIONS.md](../../e2e/CONVENTIONS.md))

## Code Quality

- [ ] No dead code, no commented-out code
- [ ] No `TODO` or `FIXME` without a linked issue
- [ ] Functions are < 30 lines (or well-justified)
- [ ] Variable names are descriptive and consistent with existing code
- [ ] No duplicated logic that should be extracted

## Documentation

- [ ] `CHANGELOG.md` updated under `[Unreleased]` if user-facing change
- [ ] API changes reflected in Pydantic schemas (auto-documented)
- [ ] Breaking changes are flagged in the commit message

## Pragmatic Checks

- [ ] The PR does ONE thing (feature, fix, or refactor — not all at once)
- [ ] No unrelated formatting changes mixed in
- [ ] The diff is reviewable in < 15 minutes (split large PRs)
- [ ] CI passes (tests + lint + type-check + build)
