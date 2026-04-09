#!/usr/bin/env bash
# ============================================================================
# Docling Studio — Automated Audit Checks (FastAPI + Vue 3 profile)
# ============================================================================
# Runs verification commands for each of the 12 release audits.
# Usage: bash profiles/fastapi-vue/commands.sh
# Run from the repository root.
# ============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

pass()  { echo -e "  ${GREEN}PASS${NC} $1"; ((PASS++)); }
warn()  { echo -e "  ${YELLOW}WARN${NC} $1"; ((WARN++)); }
fail()  { echo -e "  ${RED}FAIL${NC} $1"; ((FAIL++)); }

# ── 01. Clean Architecture ─────────────────────────────────────────────────
echo ""
echo "== 01. Clean Architecture =="

# Domain must not import from api, persistence, infra
if grep -rn "from api\|from persistence\|from infra\|import fastapi\|import aiosqlite" document-parser/domain/ 2>/dev/null; then
  fail "Domain layer imports forbidden modules"
else
  pass "Domain layer has no forbidden imports"
fi

# API must not import from persistence directly
if grep -rn "from persistence" document-parser/api/ 2>/dev/null; then
  fail "API layer imports directly from persistence"
else
  pass "API layer does not import from persistence"
fi

# ── 02. DDD ────────────────────────────────────────────────────────────────
echo ""
echo "== 02. DDD =="

# Domain models exist
if [ -f document-parser/domain/models.py ] && [ -f document-parser/domain/ports.py ]; then
  pass "Domain models and ports exist"
else
  fail "Missing domain/models.py or domain/ports.py"
fi

# Value objects exist
if [ -f document-parser/domain/value_objects.py ]; then
  pass "Value objects defined"
else
  warn "No value_objects.py in domain"
fi

# ── 03. Clean Code ─────────────────────────────────────────────────────────
echo ""
echo "== 03. Clean Code =="

# Check for files > 300 lines (backend)
LARGE_FILES=$(find document-parser -name "*.py" ! -path "*/.venv/*" ! -path "*/__pycache__/*" ! -path "*/tests/*" -exec awk 'END{if(NR>300) print FILENAME": "NR" lines"}' {} \;)
if [ -n "$LARGE_FILES" ]; then
  warn "Large Python files (>300 lines):"
  echo "$LARGE_FILES"
else
  pass "No Python files exceed 300 lines"
fi

# Check for files > 300 lines (frontend)
LARGE_VUE=$(find frontend/src -name "*.vue" -o -name "*.ts" | xargs awk 'END{if(NR>300) print FILENAME": "NR" lines"}' 2>/dev/null)
if [ -n "$LARGE_VUE" ]; then
  warn "Large frontend files (>300 lines):"
  echo "$LARGE_VUE"
else
  pass "No frontend files exceed 300 lines"
fi

# ── 04. KISS ───────────────────────────────────────────────────────────────
echo ""
echo "== 04. KISS =="

# Check for overly complex patterns
if grep -rn "type:\s*ignore" document-parser/ --include="*.py" ! -path "*/.venv/*" 2>/dev/null; then
  warn "Found type: ignore comments (review if justified)"
else
  pass "No unjustified type: ignore"
fi

# ── 05. DRY ────────────────────────────────────────────────────────────────
echo ""
echo "== 05. DRY =="

# Check for magic numbers in backend
if grep -rn "[^a-zA-Z_][0-9]\{3,\}[^0-9]" document-parser/ --include="*.py" ! -path "*/.venv/*" ! -path "*/tests/*" 2>/dev/null | grep -v "port\|version\|status\|#\|MAX_\|DEFAULT_\|LIMIT_" | head -5; then
  warn "Possible magic numbers found (review above)"
else
  pass "No obvious magic numbers"
fi

# ── 06. SOLID ──────────────────────────────────────────────────────────────
echo ""
echo "== 06. SOLID =="

# Check that ports (interfaces) exist
if grep -l "Protocol\|ABC\|abstractmethod" document-parser/domain/ports.py 2>/dev/null; then
  pass "Domain ports use Protocol/ABC (Dependency Inversion)"
else
  fail "No abstract ports found in domain"
fi

# ── 07. Decoupling ─────────────────────────────────────────────────────────
echo ""
echo "== 07. Decoupling =="

# Frontend should not hardcode backend URLs (except in config)
if grep -rn "localhost:8000\|127.0.0.1:8000" frontend/src/ --include="*.ts" --include="*.vue" 2>/dev/null | grep -v "config\|env\|http.ts"; then
  fail "Frontend hardcodes backend URL outside config"
else
  pass "Frontend backend URL is configurable"
fi

# ── 08. Security ───────────────────────────────────────────────────────────
echo ""
echo "== 08. Security =="

# Check for hardcoded secrets
if grep -rni "password\s*=\s*['\"].\+['\"\|secret\s*=\s*['\"].\+['\"\|api_key\s*=\s*['\"].\+['\"]" document-parser/ --include="*.py" ! -path "*/.venv/*" ! -path "*/tests/*" 2>/dev/null; then
  fail "Possible hardcoded secrets found"
else
  pass "No hardcoded secrets detected"
fi

# Check for eval/exec
if grep -rn "\beval(\|exec(" document-parser/ --include="*.py" ! -path "*/.venv/*" 2>/dev/null; then
  fail "eval() or exec() found in backend"
else
  pass "No eval/exec in backend"
fi

# Check CORS configuration exists
if grep -rn "CORSMiddleware" document-parser/ --include="*.py" ! -path "*/.venv/*" 2>/dev/null > /dev/null; then
  pass "CORS middleware is configured"
else
  warn "No CORS middleware found"
fi

# ── 09. Tests ──────────────────────────────────────────────────────────────
echo ""
echo "== 09. Tests =="

# Backend tests exist
BACKEND_TESTS=$(find document-parser/tests -name "test_*.py" 2>/dev/null | wc -l)
if [ "$BACKEND_TESTS" -gt 0 ]; then
  pass "Backend: $BACKEND_TESTS test files found"
else
  fail "No backend test files found"
fi

# Frontend tests exist
FRONTEND_TESTS=$(find frontend/src -name "*.test.*" 2>/dev/null | wc -l)
if [ "$FRONTEND_TESTS" -gt 0 ]; then
  pass "Frontend: $FRONTEND_TESTS test files found"
else
  fail "No frontend test files found"
fi

# E2E tests exist
E2E_TESTS=$(find e2e -name "*.feature" 2>/dev/null | wc -l)
if [ "$E2E_TESTS" -gt 0 ]; then
  pass "E2E: $E2E_TESTS feature files found"
else
  warn "No e2e feature files found"
fi

# Check for skipped tests
if grep -rn "@skip\|@ignore\|xit(\|xdescribe(\|pytest.mark.skip" document-parser/tests/ frontend/src/ 2>/dev/null | grep -v "helpers"; then
  warn "Skipped tests found (review if intentional)"
else
  pass "No skipped tests"
fi

# ── 10. CI / Build ────────────────────────────────────────────────────────
echo ""
echo "== 10. CI / Build =="

# CI workflow exists
if [ -f .github/workflows/ci.yml ]; then
  pass "CI workflow exists"
else
  fail "No CI workflow found"
fi

# Dockerfile exists
if [ -f Dockerfile ]; then
  pass "Dockerfile exists"
else
  fail "No Dockerfile found"
fi

# Health check in docker-compose
if grep -q "healthcheck" docker-compose.yml 2>/dev/null; then
  pass "Docker Compose has health check"
else
  warn "No health check in docker-compose.yml"
fi

# ── 11. Documentation ─────────────────────────────────────────────────────
echo ""
echo "== 11. Documentation =="

# CHANGELOG exists and has content
if [ -f CHANGELOG.md ] && [ -s CHANGELOG.md ]; then
  pass "CHANGELOG.md exists and is not empty"
else
  fail "CHANGELOG.md missing or empty"
fi

# README exists
if [ -f README.md ]; then
  pass "README.md exists"
else
  fail "README.md missing"
fi

# Check for TODO/FIXME without issue reference
TODOS=$(grep -rn "TODO\|FIXME" document-parser/ frontend/src/ --include="*.py" --include="*.ts" --include="*.vue" ! -path "*/.venv/*" ! -path "*/node_modules/*" 2>/dev/null | grep -v "#[0-9]" | head -5)
if [ -n "$TODOS" ]; then
  warn "TODO/FIXME without issue reference:"
  echo "$TODOS"
else
  pass "No orphaned TODO/FIXME"
fi

# ── 12. Performance ───────────────────────────────────────────────────────
echo ""
echo "== 12. Performance =="

# Check for synchronous file I/O in async context
if grep -rn "open(" document-parser/api/ document-parser/services/ --include="*.py" 2>/dev/null | grep -v "aiofiles\|async\|#"; then
  warn "Synchronous file I/O in async code (review above)"
else
  pass "No synchronous file I/O in async endpoints"
fi

# Check for N+1 patterns (loop with DB call)
if grep -rn "for.*in.*:" document-parser/services/ --include="*.py" -A5 2>/dev/null | grep "await.*repo\|await.*db"; then
  warn "Possible N+1 query pattern (review above)"
else
  pass "No obvious N+1 patterns"
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo -e "  ${GREEN}PASS${NC}: $PASS"
echo -e "  ${YELLOW}WARN${NC}: $WARN"
echo -e "  ${RED}FAIL${NC}: $FAIL"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
