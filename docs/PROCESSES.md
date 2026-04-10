# Available Processes

Index of all documented processes in Docling Studio. Each process is a structured, repeatable workflow with a clear trigger and deliverable.

---

## Development

| # | Process | Trigger / Command | Doc | Output |
|---|---------|-------------------|-----|--------|
| 1 | **Commit** | Every commit | [commit-conventions.md](git-workflow/commit-conventions.md) | Conventional Commit message |
| 2 | **Code Review** | Every PR | [code-review-checklist.md](git-workflow/code-review-checklist.md) | Reviewed PR with checklist |
| 3 | **Merge** | PR approved + CI green | [merge-policy.md](git-workflow/merge-policy.md) | Squash/merge commit on target branch |
| 4 | **ADR** | Architecture decision needed | [adr-guide.md](architecture/adr-guide.md) + [adr-template.md](architecture/adr-template.md) | `docs/architecture/adrs/ADR-NNN-*.md` |

### How to invoke

```
# Ask for a code review
Review cette PR avec docs/git-workflow/code-review-checklist.md

# Create an ADR
Crée un ADR pour [la décision à documenter]
```

---

## Quality & Audit

| # | Process | Trigger / Command | Doc | Output |
|---|---------|-------------------|-----|--------|
| 5 | **Full Release Audit** | Before merging `release/*` to `main` | [docs/audit/master.md](audit/master.md) | 12 audit reports + summary in `reports/release-X.Y.Z/` |
| 6 | **Single Audit** | Targeted check on one axis | [docs/audit/audits/*.md](audit/audits/) | Single audit report |
| 7 | **Re-Audit** | After fixing CRIT/MAJ findings | [docs/audit/master.md](audit/master.md) | Updated report |
| 8 | **Automated Checks** | Quick validation before audit | [profiles/fastapi-vue/commands.sh](../profiles/fastapi-vue/commands.sh) | PASS/WARN/FAIL per check |

### How to invoke

```
# Full audit
Audite la branche release/X.Y.Z en suivant docs/audit/master.md

# Single audit
Exécute l'audit docs/audit/audits/08-security.md sur la branche courante

# Re-audit after fixes
Re-audite les écarts CRIT et MAJ du rapport docs/audit/reports/release-X.Y.Z/summary.md

# Automated checks (shell)
bash profiles/fastapi-vue/commands.sh
```

---

## Release & Deploy

| # | Process | Trigger / Command | Doc | Output |
|---|---------|-------------------|-----|--------|
| 9 | **Release Gate** | Auto on push/PR `release/*` → `main` | [release-gate.yml](../.github/workflows/release-gate.yml) | GO / GO CONDITIONAL / NO-GO comment on PR |
| 10 | **Release** | Feature freeze on `release/*` | [CONTRIBUTING.md](../CONTRIBUTING.md#release-process) | Tag `vX.Y.Z`, Docker images on ghcr.io |
| 11 | **Deployment** | After release tag | [deployment-checklist.md](release/deployment-checklist.md) | Running instance at new version |
| 12 | **Rollback** | Post-deploy failure detected | [rollback-playbook.md](release/rollback-playbook.md) | Reverted to last known good version |
| 13 | **Hotfix** | Critical bug on released version | [CONTRIBUTING.md](../CONTRIBUTING.md#hotfix) | Patch release `vX.Y.Z+1` |

### Release Gate details

The release gate runs **automatically** on every push to `release/**` and on PRs targeting `main`. It validates 10 checks in 4 phases:

```
Phase 1 (parallel)     Phase 2 (Docker)       Phase 3 (E2E)       Phase 4
┌──────────────┐       ┌──────────────┐       ┌─────────────┐    ┌─────────────┐
│ lint+typecheck│       │ docker build │──────▶│ e2e API     │───▶│ release     │
│ unit tests   │       │ docker smoke │──────▶│ e2e UI      │    │ summary     │
│ dep audit    │       │ image scan   │       └─────────────┘    │ (PR comment)│
│ audit checks │       │ image size   │                          └─────────────┘
└──────────────┘       └──────────────┘
```

| Check | Blocks merge? | Details |
|-------|---------------|---------|
| Lint & type-check | Yes | ruff + ESLint + vue-tsc |
| Unit tests | Yes | pytest + Vitest |
| Dep audit | Yes (CRITICAL) | pip-audit + npm audit |
| Audit checks | Yes | `profiles/fastapi-vue/commands.sh` |
| Docker build | Yes | Both targets (remote + local) |
| Docker smoke | Yes | Start container, verify `/api/health` |
| Image scan (Trivy) | Yes (CRITICAL) | HIGH = warning annotation |
| Image size | No (warning) | Delta vs previous release, alert if > 10% |
| E2E API | Yes | `@smoke,@regression,@e2e` (full scope) |
| E2E UI | Yes | `@critical` |

**Verdict**: posted as a comment on the release PR:
- **GO** — all checks pass
- **GO CONDITIONAL** — blocking checks pass, dep audit or audit checks have warnings
- **NO-GO** — at least one blocking check failed

### How to invoke

```
# Release gate runs automatically — no manual trigger needed
# Just push to release/* or open a PR release/* → main

# Prepare a release
Prépare la release X.Y.Z en suivant CONTRIBUTING.md#release-process

# Deploy
Déploie en suivant docs/release/deployment-checklist.md

# Rollback
Rollback en suivant docs/release/rollback-playbook.md
```

---

## Operations

| # | Process | Trigger / Command | Doc | Output |
|---|---------|-------------------|-----|--------|
| 14 | **Incident Response** | Service down or degraded | [incident-response.md](operations/incident-response.md) | Mitigation + post-mortem |
| 15 | **Security Vulnerability** | Vuln reported | [security-response.md](operations/security-response.md) | Fix + advisory |
| 16 | **Monitoring Setup** | New deployment | [monitoring-checklist.md](operations/monitoring-checklist.md) | Monitoring configured |

### How to invoke

```
# Incident
Gère l'incident SEV-1 en suivant docs/operations/incident-response.md

# Security vulnerability
Traite la vulnérabilité signalée en suivant docs/operations/security-response.md
```

---

## Community & Governance

| # | Process | Trigger / Command | Doc | Output |
|---|---------|-------------------|-----|--------|
| 17 | **Onboarding** | New contributor | [onboarding-guide.md](community/onboarding-guide.md) | First PR merged |
| 18 | **Issue Triage** | New issue opened | [issue-triage-process.md](community/issue-triage-process.md) | Labeled + prioritized issue |
| 19 | **Roadmap Update** | Release cycle planning | [roadmap-template.md](community/roadmap-template.md) | Updated roadmap |

### How to invoke

```
# Triage issues
Trie les issues ouvertes en suivant docs/community/issue-triage-process.md

# Update roadmap
Mets à jour la roadmap en suivant docs/community/roadmap-template.md
```

---

## Quick Reference

| Category | Processes | Key doc |
|----------|-----------|---------|
| **Dev** | Commit, Review, Merge, ADR | `docs/git-workflow/` |
| **Quality** | Audit (full/single/re-audit), Auto-checks | `docs/audit/master.md` |
| **Release** | Release, Deploy, Rollback, Hotfix | `docs/release/` + `CONTRIBUTING.md` |
| **Ops** | Incident, Security, Monitoring | `docs/operations/` |
| **Community** | Onboarding, Triage, Roadmap | `docs/community/` |

---

## Standards & References

These are not processes but reference documents used by the processes above:

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Dev setup, branching, release, versioning |
| [coding-standards.md](architecture/coding-standards.md) | Naming, style, architecture rules |
| [e2e/CONVENTIONS.md](../e2e/CONVENTIONS.md) | Karate / Karate UI test conventions |
| [architecture.md](architecture.md) | System architecture (backend + frontend) |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Community behavior standards |
| [SECURITY.md](../SECURITY.md) | Vulnerability reporting policy |
| [profiles/fastapi-vue/profile.md](../profiles/fastapi-vue/profile.md) | Stack layer mapping for audits |
