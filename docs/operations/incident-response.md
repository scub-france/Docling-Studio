# Incident Response

## Severity Levels

| Level | Description | Examples | Response time |
|-------|-------------|----------|---------------|
| **SEV-1** | Service down, data loss, security breach | App unreachable, DB corrupted, credentials leaked | Immediate |
| **SEV-2** | Major feature broken, degraded for all users | Upload fails, analysis crashes, blank pages | < 2 hours |
| **SEV-3** | Minor feature broken, workaround exists | Bbox overlay misaligned, locale missing a key | Next business day |

## Response Steps

### 1. Detect

- Health endpoint returns error (`/api/health`)
- User report via GitHub issue
- CI/CD pipeline failure on `main`
- Docker container crash loop

### 2. Assess

- Determine severity (SEV-1/2/3)
- Identify affected component: backend, frontend, Docker, CI
- Check recent deployments: `git log --oneline -10 main`

### 3. Communicate

- **SEV-1**: Notify all maintainers immediately
- **SEV-2**: Open a GitHub issue with `priority: P0` label
- **SEV-3**: Open a GitHub issue with `priority: P1` label

### 4. Mitigate

**Rollback first, investigate later.**

- If the issue appeared after a deploy → [rollback](../release/rollback-playbook.md)
- If the issue is in a specific endpoint → disable the route or return a maintenance response
- If the issue is in Docling itself → switch to remote mode (`CONVERSION_ENGINE=remote`)

### 5. Fix

- Create a `hotfix/*` branch from the last stable tag
- Fix the root cause, add a regression test
- Run the [release audit](../audit/master.md) on the fix
- Deploy via the [deployment checklist](../release/deployment-checklist.md)

### 6. Post-Mortem

Write a post-mortem for SEV-1 and SEV-2 incidents using this template:

```markdown
# Post-Mortem: [Incident Title]

**Date**: YYYY-MM-DD
**Severity**: SEV-X
**Duration**: Xh Xm
**Author**: [name]

## Timeline

| Time | Event |
|------|-------|
| HH:MM | Incident detected |
| HH:MM | Severity assessed |
| HH:MM | Mitigation applied |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Incident resolved |

## Root Cause

[What actually broke and why]

## Impact

[Who was affected, for how long, what data was at risk]

## What Went Well

- ...

## What Went Wrong

- ...

## Action Items

| Action | Owner | Due |
|--------|-------|-----|
| ... | ... | ... |
```

Store post-mortems in `docs/operations/post-mortems/YYYY-MM-DD-short-title.md`.
