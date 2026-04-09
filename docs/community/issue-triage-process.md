# Issue Triage Process

How we classify, prioritize, and manage GitHub issues.

## Labels

### Type

| Label | Description |
|-------|-------------|
| `bug` | Something is broken |
| `feature` | New functionality |
| `enhancement` | Improvement to existing functionality |
| `docs` | Documentation only |
| `question` | Support / how-to question |
| `chore` | Tooling, CI, dependencies |

### Priority

| Label | Response SLA | Fix SLA | Description |
|-------|-------------|---------|-------------|
| `priority: P0` | Same day | < 3 days | Critical — service down, data loss, security |
| `priority: P1` | < 3 days | < 2 weeks | High — major feature broken, no workaround |
| `priority: P2` | < 1 week | Next release | Medium — feature degraded, workaround exists |
| `priority: P3` | < 2 weeks | Backlog | Low — minor, cosmetic, nice-to-have |

### Status

| Label | Description |
|-------|-------------|
| `needs-info` | Waiting for reporter to provide more details |
| `confirmed` | Bug reproduced or feature accepted |
| `good-first-issue` | Suitable for new contributors |
| `help-wanted` | Open for community contribution |
| `wont-fix` | Intentional behavior, out of scope, or won't be addressed |
| `duplicate` | Already tracked in another issue |
| `stale` | No activity for 30 days |

### Component

| Label | Maps to |
|-------|---------|
| `component: backend` | `document-parser/` |
| `component: frontend` | `frontend/` |
| `component: e2e` | `e2e/` |
| `component: docker` | Docker / docker-compose |
| `component: ci` | `.github/workflows/` |

## Triage Workflow

```
New issue
  │
  ├─ Missing info? → label `needs-info`, comment asking for details
  │                   (auto-close after 14 days if no response)
  │
  ├─ Duplicate? → label `duplicate`, link to original, close
  │
  ├─ Out of scope? → label `wont-fix`, explain why, close
  │
  └─ Valid issue
      │
      ├─ Add type label (bug / feature / enhancement / ...)
      ├─ Add component label
      ├─ Assess priority (P0 / P1 / P2 / P3)
      ├─ If simple → add `good-first-issue`
      └─ Assign to milestone (if applicable)
```

## Stale Policy

| Condition | Action |
|-----------|--------|
| No activity for **30 days** | Bot labels `stale` + comment |
| No activity for **14 more days** | Bot closes the issue |
| Reporter responds | `stale` label removed, timer resets |

Issues labeled `priority: P0` or `priority: P1` are exempt from the stale policy.

## Response Expectations

- **Every issue gets a response** (even if it's "thanks, we'll look at this next week")
- Acknowledge within the SLA for the priority level
- If you can't fix it soon, say so — don't leave reporters hanging
- Close issues with a comment explaining the resolution
