# Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) to keep the git history readable and to enable automated changelog generation.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Types

| Type | When to use | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(chunking): add hierarchical chunker support` |
| `fix` | Bug fix | `fix(upload): handle empty PDF gracefully` |
| `docs` | Documentation only | `docs: update architecture diagram` |
| `style` | Formatting, no logic change | `style(api): fix ruff formatting warnings` |
| `refactor` | Code restructuring, no behavior change | `refactor(persistence): extract repository base class` |
| `test` | Adding or updating tests | `test(analysis): add rechunk edge case tests` |
| `chore` | Tooling, CI, dependencies | `chore: bump docling to 2.31` |
| `perf` | Performance improvement | `perf(bbox): batch coordinate normalization` |
| `ci` | CI/CD pipeline changes | `ci: add multi-arch Docker build` |

## Scopes (optional)

Use the feature or component name:

| Scope | Maps to |
|-------|---------|
| `api` | `document-parser/api/` |
| `domain` | `document-parser/domain/` |
| `persistence` | `document-parser/persistence/` |
| `infra` | `document-parser/infra/` |
| `upload` | Upload feature (front + back) |
| `analysis` | Analysis feature (front + back) |
| `chunking` | Chunking feature (front + back) |
| `bbox` | Bounding box pipeline |
| `e2e` | `e2e/` tests |
| `docker` | Dockerfile, docker-compose |
| `ci` | `.github/workflows/` |

## Rules

1. **Subject line** — imperative mood, lowercase, no period, max 72 characters
2. **Body** — explain *why*, not *what* (the diff shows what)
3. **Breaking changes** — add `BREAKING CHANGE:` in the footer or `!` after the type: `feat(api)!: rename /analyses to /jobs`
4. **Issue references** — use `Closes #123` or `Fixes #456` in the footer

## Examples

```
feat(chunking): add page filtering in Prepare mode

Users can now select which pages to include in chunking.
The filter is persisted in the analysis job metadata.

Closes #87
```

```
fix(upload): reject files exceeding MAX_FILE_SIZE_MB

Previously, oversized files were accepted and failed silently
during Docling conversion. Now the API returns 413 with a
clear error message.

Fixes #102
```
