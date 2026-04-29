# Rapport d'audit : Tests

**Release** : 0.5.0  
**Date** : 2026-04-28  
**Auditeur** : claude-code  

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 17 / 18 |
| Score | 94 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 1 |
| Ecarts MINOR | 0 |
| Ecarts INFO | 0 |

---

## Ecarts constates

### [MAJ] 18 assertions vagues "assert X is not None"

- **Localisation** : `document-parser/tests/test_local_converter.py:70`, `test_repos.py:42,95,124,190,192`, `test_ingestion_service.py:119`, `test_analysis_service.py:354`, `test_models.py:61,77,87`, `test_chunking.py:276`, `test_api_endpoints.py:199`, `test_vector_store_port.py:47`, `test_pipeline_options.py:56`, `neo4j/test_document_roundtrip.py:24`, `neo4j/test_tree_writer.py:204`, `neo4j/test_chunk_writer.py:97`, `test_opensearch_store.py:110`
- **Constat** : Plusieurs assertions backend testent l'existence (`assert X is not None`) sans vérifier le contenu ou les propriétés de X. Ces assertions ne capturent que la présence, pas la correction.
- **Regle violee** : 9.3.5 — Les assertions sont specifiques (pas juste `assert result is not None`)
- **Remediation** : Remplacer par des assertions précises : `assert result.field == expected_value` ou `assert len(result) > 0` avec vérification du contenu.
- **Poids** : 2 (MAJOR) — Impact modéré sur la qualité des tests d'intégration

---

## Points positifs

1. **Couverture d'endpoints robuste** (9.2.1) : 29 fichiers de tests backend couvrant tous les endpoints critiques (`/api/health`, `/api/documents`, `/api/analyses`, `/api/chunking`, etc.). Chaque endpoint a au moins un happy path avec TestClient.

2. **Test d'erreurs complets** (9.2.2) : Les tests couvrent 400, 404, et gestion d'erreurs métier. Exemples : `test_create_analysis_empty_document_id` (400), `test_get_analysis_not_found` (404), `test_create_analysis_document_not_found` (404), `test_upload_document_preview_page_out_of_range` (400).

3. **Services bien testés** (9.2.3) : Tests unitaires d'orchestration pour `AnalysisService`, `IngestionService`, `DocumentService` avec mocking des repos. Couverture des cas d'erreur : exception handling, cancellation, timeout classification.

4. **Domain value objects testes** (9.2.4) : `test_bbox.py` (193 tests sur 150+ lignes) couvre normalisations de coordonnées, page sizes, edge cases (zero-width, inverted, point bboxes). `test_chunking.py` teste `ChunkingOptions` avec defaults et custom values. `test_models.py` teste les state transitions.

5. **Composants Vue et stores critiques testes** (9.2.5) : 23 tests frontend colocalises (`*.test.ts`) couvrant stores Pinia (`ingestion/store.test.ts`, `analysis/store.test.ts`, `document/store.test.ts`, `feature-flags/store.test.ts`), composables (`useFeatureFlag.test.ts`), et API layers (`ingestion/api.test.ts`, `analysis/api.test.ts`).

6. **Pas d'anti-patterns de test** (9.3.1, 9.3.2) : Aucun `.only`, `fdescribe`, `fit`, ou `.skip()` sans justification trouvé. Tous les tests actifs et exécutés.

7. **Determinisme garanti** (9.3.3) : 
   - Backend : pytest avec `asyncio_mode = auto`. Pas de `sleep()` ou dépendances réseau brutes trouvées.
   - Frontend : Vitest avec `vi.useFakeTimers()` / `vi.useRealTimers()` dans tests d'orchestration (polling, intervals). Mocks d'API systématiques (`vi.mock('./api')`).

8. **Mocking vs integration equilibre** (9.3.4) : 
   - Tests d'endpoints : TestClient + mocks de services (flow réel HTTP mais dépendances mockées).
   - Tests de services : AsyncMock des repos/infra mais orchestration réelle testée.
   - E2E Karate UI : vrais workflows UI ; Karate API tests : vrais appels HTTP.

9. **Nommage explicite** (9.3.6) : Tous les tests ont des noms clairs décrivant le comportement. Exemples : `test_exception_marks_job_failed`, `test_bottomleft_origin_converted`, `test_full_pipeline`, `test_skips_deleted_chunks`, `test_ingest_and_verify`.

10. **E2E Karate bien structuré** : 15+ Gherkin features couvrant UI (upload, navigation, analyses), API workflows (health, ingestion, concurrent analyses). Conventions respectées (Background, waitFor, cleanup). UIRunner et E2ERunner organisent tests par tags (@critical, @ui, @smoke).

---

## Verdict partiel : GO

**Justification** : 
- Score 94/100 dépasse le seuil GO (>= 80).
- Zero écarts CRITICAL — aucune violation bloquante.
- Un écart MAJOR (assertions vagues) est non-bloquant selon master.md §3 ("GO CONDITIONNEL si <= 3 MAJOR et 0 CRITICAL"). Cet écart est facilement corrigible en post-release.
- Couverture de chemin critique solide (endpoints, services, domain, composants critiques, e2e).
- Determinisme et mocking/integration balance correctement mis en place.

**Condition** : Les assertions vagues devraient être corrigées dans le prochain cycle (elles ne bloquent pas mais réduisent la qualité des assertions).
