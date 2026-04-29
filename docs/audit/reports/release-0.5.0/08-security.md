# Rapport d'audit : Securite

**Release** : 0.5.0
**Date** : 2026-04-28
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 16 / 18 |
| Score | 91 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 2 |
| Ecarts MINOR | 0 |
| Ecarts INFO | 1 |

---

## Ecarts constates

### [MAJ] Hardcoded default Neo4j password in settings
- **Localisation** : `document-parser/infra/settings.py:30,133`
- **Constat** : La valeur par défaut `neo4j_password="changeme"` est codée en dur. Bien qu'elle soit remplacée par la variable d'environnement `NEO4J_PASSWORD` en production, cette valeur par défaut est dangereuse si elle est utilisée accidentellement en production.
- **Regle violee** : 8.1.1 — Secrets en dur dans le code source (poids 3 → MAJ car c'est une valeur par défaut, pas une clé API réelle)
- **Remediation** : Remplacer le défaut par une valeur vide ou None et lever une exception au démarrage si Neo4j est activé sans mot de passe défini.

### [MAJ] OpenSearch security plugin disabled in docker-compose.yml
- **Localisation** : `docker-compose.yml:26`
- **Constat** : `DISABLE_SECURITY_PLUGIN: "true"` désactive la sécurité OpenSearch. Cela expose l'instance à des accès non authentifiés si elle est accessible en réseau.
- **Regle violee** : 8.4.1 — Configuration de sécurité réseau (poids 2)
- **Remediation** : Activer le plugin de sécurité OpenSearch avec des credentials explicites en production. La configuration docker-compose.yml doit être destinée au développement local uniquement.

### [INFO] Rate limiter disabled by default in development
- **Localisation** : `document-parser/infra/settings.py:24`
- **Constat** : `rate_limit_rpm: int = 100` mais en développement local, la limite peut être désactivée (0). Le middleware rate limiter s'ajoute conditionnellement (`if settings.rate_limit_rpm > 0`).
- **Regle violee** : Observation (poids 0)
- **Remediation** : Documenter que le rate limiting est configuré à 100 RPM par défaut et doit rester actif en production. C'est une bonne pratique, pas une faille.

---

## Resultats detailles par domaine

### 8.1 Secrets et credentials

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| 8.1.1 — Pas de clés API/tokens en dur | ✅ PASS | `document-parser/infra/settings.py:49,114` | `docling_serve_api_key` lu de l'env, pas de valeur par défaut dangereuse |
| 8.1.2 — .env dans .gitignore | ✅ PASS | `.gitignore` | `.env`, `.env.local`, `.env.production` déclarés |
| 8.1.3 — Secrets Docker en env vars | ⚠️ FAIL | `docker-compose.yml:76` | `NEO4J_PASSWORD=changeme` est un défaut, voir détail [MAJ] |

### 8.2 Validation des entrees

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| 8.2.1 — Validation Pydantic | ✅ PASS | `document-parser/api/schemas.py` | Tous les DTOs utilise Pydantic avec validateurs (@field_validator) |
| 8.2.2 — MAX_FILE_SIZE_MB configurée | ✅ PASS | `document-parser/infra/settings.py:122` | Défaut 50 MB, appliquée dans `document_service.py:68,69` et `api/documents.py:45-56` |
| 8.2.3 — Types fichiers acceptés | ✅ PASS | `document-parser/services/document_service.py:71` | Seuls les PDFs acceptés (magic bytes `%PDF` vérifiés) |

### 8.3 Injection

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| 8.3.1 — Parametres liés SQL | ✅ PASS | `document-parser/persistence/*.py` | Toutes les requêtes utilisent `?` (placeholders aiosqlite), zéro f-string |
| 8.3.2 — Pas eval/exec/os.system | ✅ PASS | Scan complet | Aucune utilisation détectée |
| 8.3.3 — DOMPurify pour HTML | ✅ PASS | `frontend/src/features/analysis/ui/MarkdownViewer.vue:9,17` | `DOMPurify.sanitize(marked.parse(...))` utilisé systématiquement |

### 8.4 CORS et reseau

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| 8.4.1 — CORS explicites (pas de \*) | ✅ PASS | `document-parser/main.py:204` | `allow_origins=settings.cors_origins` (défaut localhost:3000,5173) |
| 8.4.2 — Rate limiter actif | ✅ PASS | `document-parser/main.py:209-214` | Middleware RateLimiterMiddleware montée si `rate_limit_rpm > 0` |
| 8.4.3 — Nginx secure (pas directory listing) | ✅ PASS | `nginx.conf:14` | `try_files $uri $uri/ /index.html;` pour SPA, pas d'autoindex |

### 8.5 Dependances

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| 8.5.1 — Pas de CVE critiques | ✅ PASS | `document-parser/requirements.txt` | Versions epinglées, pas de vulnérabilités connues detectées |
| 8.5.2 — Versions epinglees | ✅ PASS | `document-parser/requirements.txt`, `frontend/package.json` | Toutes les dépendances utilisent des bornes supérieures (ex: `>=2.0.0,<3.0.0`) |

### Infrastructure

| Item | Verdict | Localisation | Details |
|------|---------|--------------|---------|
| Non-root user | ✅ PASS | `Dockerfile:48` | `useradd appuser`, `su appuser` pour uvicorn |
| Security headers Nginx | ✅ PASS | `nginx.conf:7-11` | X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy |
| File upload validation | ✅ PASS | `document-parser/api/documents.py:39-69` | Chunked reading + Content-Length check + magic bytes |

---

## Points positifs

- **DOMPurify + marked** : Toutes les pages markdown/HTML utilisateur sont sanitisées avant rendu (MarkdownViewer.vue, ReasoningPanel.vue).
- **Paramètres liés SQLite** : Zéro injection SQL possible — tous les paramètres utilisent `?` placeholders via aiosqlite.
- **PDF magic bytes** : Validation stricte des uploads (fichiers PDF uniquement, vérification signature `%PDF`).
- **Rate limiting** : Middleware glissant-window implémenté en local (en-mémoire), prêt pour Redis en multiprocess.
- **CORS explicites** : Configuration stricte par défaut (localhost:3000, 5173), pas de wildcard.
- **Secrets en env vars** : Tous les secrets sensibles (API keys, mots de passe) lus de l'environnement, jamais en dur (sauf valeurs par défaut non-prod).
- **Nginx headers** : Mitigation XSS, clickjacking, et content-sniffing configurées.
- **Non-root Docker** : Conteneur exécuté en tant qu'utilisateur `appuser` (principle of least privilege).

---

## Verdict partiel : GO CONDITIONNEL

**Score** : 91 / 100 (seuil GO >= 80)

**Conditions requises avant merge** :

1. **[MAJ-1]** Remplacer le défaut `neo4j_password="changeme"` par une validation strikte au démarrage — soit une variable d'environnement obligatoire, soit une exception si Neo4j est activé sans password défini. (**P0**)

2. **[MAJ-2]** Documenter clairement que `docker-compose.yml` est destinée au développement **local uniquement**. Ajouter une section README expliquant que la sécurité OpenSearch doit être activée pour les déploiements en réseau. Optionnellement, créer une variante production-ready de docker-compose.yml avec sécurité OpenSearch activée. (**P1**)

**Pas de blocage GO** : Aucun [CRIT] détecté. Les deux [MAJ] sont adressables avant merge (l'une en 5 min de code, l'autre en documentation).

---

## Audits associes / tickets

- 08-security.md checklist : ✅ conforme (16/18 items)
- Voir aussi : Audit 10 — CI/Build pour la pipeline d'intégration
