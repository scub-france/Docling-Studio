# Rapport d'audit : CI / Build

**Release** : 0.5.0  
**Date** : 2026-04-28  
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 10 / 11 |
| Score | 91 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 1 |
| Ecarts MINOR | 0 |
| Ecarts INFO | 0 |

---

## Ecarts constates

### [MAJ] Ruff warning UP038 — isinstance() union syntax not applied

- **Localisation** : `document-parser/infra/docling_tree.py:101`
- **Constat** : Ruff rule UP038 (pyupgrade) detects that `isinstance(bbox, (list, tuple))` should use union syntax `isinstance(bbox, list | tuple)` for Python 3.12+ consistency.
- **Regle violee** : 10.1.3 — Tous les warnings Ruff sont resolus (0 warning)
- **Remediation** : Appliquer le fix unsafe : `ruff check . --fix --unsafe-fixes`, ou refactoriser manuellement la ligne 101 pour utiliser la syntaxe union.

---

## Points positifs

- **Pipeline CI robuste** : Workflows bien structures (ci.yml, release-gate.yml) avec phases paralleles et E2E complets (API + UI).
- **.dockerignore complet** : Exclut correctement node_modules, .venv, .git, __pycache__ et autres artefacts inutiles.
- **Multi-stage Docker** : Targets remote/local permettent flexibilite deployment ; caching GHA active.
- **Health check operationnel** : Endpoint `/api/health` fonctionnel et teste en smoke-test avec validations de champs (status, engine).
- **Nginx bien configure** : Routing `/api/*` → backend 127.0.0.1:8000, frontend statique sur `/`, timeouts 900s acceptables.
- **Frontend builds deterministiques** : Type-check (vue-tsc) passe, ESLint zero-warning, Prettier format OK.
- **Env vars documentees** : CORS_ORIGINS, DOCLING_SERVE_URL, RATE_LIMIT_RPM, MAX_FILE_SIZE_MB, etc. avec defaults cohaerents.

---

## Verdict partiel : GO CONDITIONNEL

**Conditions** :
- Resoudre l'ecart MAJOR 10.1.3 : appliquer le fix Ruff UP038 a docling_tree.py:101 et reverifier `ruff check .` avant le merge final.

**Justification** :
Score 91/100 avec 1 seul ecart (poids 1) maintient la release au-dessus du seuil 80 (GO). Aucun ecart CRITICAL. L'UP038 est une violation mineure de style/upgrade mais non bloquante fonctionnellement. La remediation est triviale (un fix unsafe ou 2 lignes manuelles).

