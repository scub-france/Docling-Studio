# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes       |
| < 0.3   | No        |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report them privately:

1. **Email**: Send a detailed report to **[INSERT SECURITY EMAIL]**
2. **GitHub Security Advisory**: Use [GitHub's private vulnerability reporting](https://github.com/scub-france/Docling-Studio/security/advisories/new)

### What to include

- Description of the vulnerability
- Steps to reproduce
- Affected component(s): `document-parser/`, `frontend/`, `docker-compose.yml`, etc.
- Impact assessment (data exposure, denial of service, privilege escalation, etc.)
- Suggested fix (if any)

### Response timeline

| Step | SLA |
|------|-----|
| Acknowledgment | < 48 hours |
| Initial assessment | < 7 days |
| Fix developed | < 14 days (critical), < 30 days (other) |
| Public disclosure | After fix is released |

### Process

1. We acknowledge your report and assign a severity level
2. We develop a fix in a **private branch** (never pushed publicly before the advisory)
3. We release the fix and publish a GitHub Security Advisory
4. We credit the reporter (unless they prefer anonymity)

## Security Best Practices (for contributors)

- Never commit secrets, API keys, or credentials
- Never disable CORS or security middleware without review
- Validate all user input at the API boundary
- Keep dependencies up to date (`pip audit`, `npm audit`)
- Follow the [OWASP Top 10](https://owasp.org/www-project-top-ten/) guidelines
