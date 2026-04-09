# Security Vulnerability Response

Process for handling reported security vulnerabilities. See also [SECURITY.md](../../SECURITY.md) for the public-facing policy.

## Response Timeline

| Step | SLA | Action |
|------|-----|--------|
| **Acknowledge** | < 48h | Confirm receipt to the reporter |
| **Assess** | < 7 days | Determine severity (Critical / High / Medium / Low) |
| **Fix** | < 14 days (Critical), < 30 days (other) | Develop and test the fix |
| **Release** | Same day as fix | Publish patched version |
| **Disclose** | After release | Publish GitHub Security Advisory |

## Severity Assessment

| Severity | Criteria | Example |
|----------|----------|---------|
| **Critical** | Remote exploitation, data breach, no auth required | SQL injection in upload endpoint |
| **High** | Significant impact, some conditions required | Path traversal on file download |
| **Medium** | Limited impact or requires authenticated access | XSS in analysis results display |
| **Low** | Minimal impact, theoretical only | Information disclosure in error messages |

## Fix Process

1. **Create a private branch** — never push vulnerability details to a public branch before the fix is released
2. **Develop the fix** — include a regression test
3. **Run the security audit** — `docs/audit/audits/08-security.md`
4. **Review** — at least one maintainer must review the fix
5. **Release** — tag, build, deploy (see [deployment checklist](../release/deployment-checklist.md))
6. **Publish advisory** — GitHub Security Advisory with CVE if applicable

## Advisory Template

```markdown
# Security Advisory: [Title]

**Severity**: Critical | High | Medium | Low
**Affected versions**: < X.Y.Z
**Fixed in**: X.Y.Z
**CVE**: CVE-YYYY-NNNNN (if assigned)

## Description

[What the vulnerability is, without providing exploitation details]

## Impact

[What an attacker could do]

## Mitigation

[Upgrade to X.Y.Z or apply workaround]

## Credit

[Reporter name, unless they prefer anonymity]
```

## Dependency Vulnerabilities

Run regular dependency audits:

```bash
# Backend
cd document-parser && pip audit

# Frontend
cd frontend && npm audit
```

For known vulnerabilities in dependencies:
- **Critical/High**: Update immediately, release a patch version
- **Medium/Low**: Include in the next planned release
