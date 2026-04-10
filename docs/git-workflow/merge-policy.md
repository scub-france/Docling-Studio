# Merge Policy

## Merge Requirements

Every PR must meet these conditions before merging:

1. **CI green** — all checks pass (tests, lint, type-check, build)
2. **At least 1 approval** from a maintainer
3. **No unresolved conversations** — all review comments addressed
4. **Branch up to date** with target branch (rebase or merge from target)
5. **CHANGELOG updated** — if the change is user-facing

## Merge Strategy

| Branch type | Merge method | Why |
|-------------|-------------|-----|
| `feature/*` → `main` | **Squash merge** | Clean history — one commit per feature |
| `fix/*` → `main` | **Squash merge** | Clean history — one commit per fix |
| `fix/*` → `release/*` | **Squash merge** | Same rationale |
| `release/*` → `main` | **Merge commit** | Preserves the release branch history |
| `hotfix/*` → `main` | **Squash merge** | One atomic fix |

### Squash merge commit message

When squashing, the final commit message should follow [Conventional Commits](commit-conventions.md):

```
feat(chunking): add page filtering in Prepare mode (#87)
```

The PR number is appended automatically by GitHub.

## Stale PR Policy

| Condition | Action |
|-----------|--------|
| No activity for **14 days** | Maintainer pings the author |
| No activity for **30 days** | PR labeled `stale` |
| No activity for **45 days** | PR closed with comment (can be reopened) |

Draft PRs are exempt from the stale policy.

## Conflict Resolution

- **Rebase preferred** over merge commits for feature/fix branches
- If conflicts are complex, merge from target branch into the PR branch
- Never force-push a branch that has active reviewers without warning them

## Branch Cleanup

- Feature and fix branches are **deleted after merge** (GitHub auto-delete enabled)
- Release branches are kept until the next minor release
- Tags are never deleted
