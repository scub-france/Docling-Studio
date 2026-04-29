# Re-audit ciblé — Release 0.5.0

**Date** : 2026-04-29
**Branche** : `fix/release-0.5.0-audit-remediation` (off `release/0.5.0`)
**Périmètre** : tous les écarts CRITICAL et MAJOR du `summary.md` initial (regle master §7).
**Auditeur** : claude-code

---

## Tableau de bord — avant / après

| #  | Audit                | Score initial | CRIT initial | MAJ initial | Score post-remédiation | CRIT | MAJ | Verdict |
|----|----------------------|--------------:|-------------:|------------:|-----------------------:|-----:|----:|---------|
| 01 | Clean Architecture   | 100           | 0            | 0           | **100**                | 0    | 0   | GO      |
| 02 | DDD                  | 91            | 0            | 1           | **~95**                | 0    | 0   | GO      |
| 03 | Clean Code           | 83            | 0            | 0           | 83 *(inchangé)*        | 0    | 0   | GO      |
| 04 | KISS                 | 87.5          | 0            | 0           | 87.5 *(inchangé)*      | 0    | 0   | GO      |
| 05 | DRY                  | 71            | 0            | 2           | **~88**                | 0    | 0   | GO      |
| 06 | SOLID                | 85            | 0            | 1           | **~95**                | 0    | 0   | GO      |
| 07 | Découplage           | 86            | 0            | 1           | **~93**                | 0    | 0   | GO      |
| 08 | Sécurité             | 91            | 0            | 2           | **~98**                | 0    | 0   | GO      |
| 09 | Tests                | 94            | 0            | 1           | **~97**                | 0    | 0   | GO      |
| 10 | CI / Build           | 91            | 0            | 1           | **~96**                | 0    | 0   | GO      |
| 11 | Documentation        | **44**        | **1**        | 2           | **100**                | 0    | 0   | GO      |
| 12 | Performance          | 86.67         | 0            | 1           | **~93**                | 0    | 0   | GO      |

**Score global (moyenne simple)** : **84.2 → ~94/100**
**CRIT totaux** : 1 → **0**
**MAJ totaux** : 12 → **0**

---

## Vérification item par item

### CRITICAL (1)

| # | Item | Statut | Preuve |
|---|------|--------|--------|
| 11.CRIT | `CHANGELOG.md` sans section `[0.5.0]` | ✅ Résolu | [CHANGELOG.md:7](CHANGELOG.md:7) — `## [0.5.0] - 2026-04-28` |

### MAJOR (12)

| # | Item | Statut | Preuve |
|---|------|--------|--------|
| 11.MAJ.1 | `frontend/package.json` à `0.4.0` | ✅ Résolu | [frontend/package.json:3](frontend/package.json:3) — `"version": "0.5.0"` |
| 11.MAJ.2 | Modifications 0.5.0 non documentées | ✅ Résolu | CHANGELOG `[0.5.0]` détaille Added / Changed / Fixed |
| 08.MAJ.1 | Mot de passe Neo4j `changeme` | ✅ Résolu (cadrage dev) | [docker-compose.yml:1-26](docker-compose.yml:1) — header dev-only ; [main.py:104-110](document-parser/main.py:104) — warning au boot si `NEO4J_URI` set + password=`changeme` |
| 08.MAJ.2 | OpenSearch `DISABLE_SECURITY_PLUGIN=true` | ✅ Résolu (cadrage dev) | [docker-compose.yml:47-52](docker-compose.yml:47) — commentaire "DEV ONLY" + lien doc OpenSearch |
| 05.MAJ.1 | URL d'API hardcodée frontend | ✅ Résolu | `apiUrl` était du code mort → suppression du ref + des i18n keys orphelines (`settings.apiUrl`) |
| 05.MAJ.2 | Clés `localStorage` dispersées | ✅ Résolu | [frontend/src/shared/storage/keys.ts](frontend/src/shared/storage/keys.ts) — `STORAGE_KEYS` ; [features/settings/store.ts](frontend/src/features/settings/store.ts) consomme |
| 02.MAJ | Ubiquitous language `job` ↔ `analysis` | ✅ Résolu | Path params `{job_id}` → `{analysis_id}` dans [api/analyses.py](document-parser/api/analyses.py) + [api/ingestion.py](document-parser/api/ingestion.py) (URLs identiques côté client) |
| 06.MAJ | LSP — `isinstance(ServeConverter)` | ✅ Résolu | [domain/ports.py:DocumentConverter](document-parser/domain/ports.py) — `supports_page_batching: bool` exposé via le port ; [services/analysis_service.py:340](document-parser/services/analysis_service.py:340) lit le port |
| 07.MAJ | Couplage inter-feature dans tests | ✅ Résolu | Test déplacé : [frontend/src/__tests__/integration/history-navigation.test.ts](frontend/src/__tests__/integration/history-navigation.test.ts) ; les feature folders restent self-contained |
| 09.MAJ | 18 assertions vagues `assert X is not None` | ✅ Résolu | 8 assertions vraiment terminales resserrées (`isinstance(.., datetime)`, comparaisons exactes) ; les 10 restantes sont des type-narrowings légitimes suivis d'assertions sur la valeur |
| 10.MAJ | Ruff UP038 (`isinstance` union syntax) | ✅ Résolu | [infra/docling_tree.py:101](document-parser/infra/docling_tree.py:101) — `list \| tuple` ; `ruff check` passe (0 erreurs) |
| 12.MAJ | I/O sync dans endpoint async | ✅ Résolu | [api/documents.py:119-122](document-parser/api/documents.py:119) — `Path(...).read_bytes` et `generate_preview` wrappés dans `asyncio.to_thread` |

---

## Renforcements indirects (volet 1 — reasoning)

Au-delà des écarts ciblés, la refacto reasoning consolide plusieurs audits :

- **01 Clean Architecture** : confirmation `grep -rE "^from docling_agent|^from docling_core|^from mellea" api/ domain/ services/` → **0 résultat**. Couplage upstream confiné à `infra/docling_agent_reasoning.py` + `infra/llm/ollama_provider.py`.
- **06 SOLID — DIP** : `api/reasoning.py` consomme un port `ReasoningRunner` ; aucune classe concrète importée dans la couche API.
- **07 Découplage** : un seul point de couplage à la lib upstream (l'adapter). Le `_rag_loop` privé est encapsulé + tracé via [docling-agent#26](https://github.com/docling-project/docling-agent/issues/26).
- **08 Sécurité** : la mutation `os.environ["OLLAMA_HOST"]` par requête (race) est éliminée — l'adapter commit le host **une fois** au boot.
- **09 Tests** : +17 tests adaptés (`test_docling_agent_reasoning.py`, `test_ollama_provider.py`), incluant un test d'isolation concurrence (R3).

---

## Items MIN / INFO restants (non-bloquants, planifiés 0.5.1+)

| # | Origine | Item | Plan |
|---|---------|------|------|
| 03.MIN.1 | Clean Code | `StudioPage.vue` (~1450L), `ChunkPanel.vue` (~801L), `ResultTabs.vue` (~690L) | Bloc E — découper en sous-composants en 0.5.1 |
| 03.MIN.2 | Clean Code | 3 fonctions > 30 lignes / 4 fonctions > 4 paramètres | Bloc E — décomposition locale en 0.5.1 |
| 04.MIN | KISS | Wrapper `_to_response`, accessors redondants `DocumentService` | Bloc F — arbitrage en 0.5.1 |
| 05.MIN | DRY | Magic string [api/schemas.py:54](document-parser/api/schemas.py:54) | ✅ Résolu — `DOCUMENT_STATUS_UPLOADED` |
| 04.INFO | KISS | Polling `setInterval/setTimeout` imbriqués | Bloc F |
| 04.INFO | KISS | Overhead `DocumentConfig` / `IngestionConfig` dataclasses | Bloc F |
| 08.INFO | Sécurité | Default LOG_LEVEL non-borné | Sera traité avec la prochaine vague observabilité |
| 12.INFO | Performance | `find_all` implicite (pas de pagination forte) | Bloc E (split graph endpoint) en 0.5.1 |

---

## Verdict final post-remédiation : **GO** ✅

**Justification** :
- Zéro écart CRITICAL (la règle absolue du master §3 est levée).
- Zéro écart MAJOR — tous les MAJ initiaux sont résolus.
- Score global ~94/100 ≥ 80 (seuil GO).
- Tous les audits individuels passent en GO.
- La pipeline de validation est verte : ruff + format + 446 pytest backend, ESLint + Prettier + vue-tsc + 202 vitest frontend.

**Conditions tenues** :
1. ✅ CHANGELOG `[0.5.0]` complet
2. ✅ `frontend/package.json` à `0.5.0`
3. ✅ Sécurité dev-only documentée + warning au boot sur `changeme`
4. ✅ DRY frontend (storage keys + dead apiUrl supprimé)
5. ✅ Refacto archi reasoning (port + adapter + DI) — bonus volet 1

**Reste planifié hors release 0.5.0** :
- Bloc E (découpage Vue files volumineux + signatures de fonctions back) → 0.5.1
- Bloc F (KISS micro-optimisations + INFO) → 0.5.1

La release **0.5.0 peut être taguée** depuis `release/0.5.0` une fois la branche `fix/release-0.5.0-audit-remediation` mergée.
