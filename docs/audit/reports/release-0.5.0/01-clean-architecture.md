# Rapport d'audit : Hexagonal Architecture (ports & adapters)

**Release** : 0.5.0  
**Date** : 2026-04-28  
**Auditeur** : claude-code

---

## Score de compliance

| Métrique | Valeur |
|----------|--------|
| Items conformes | 14 / 14 |
| Score | 100 / 100 |
| Écarts CRITICAL | 0 |
| Écarts MAJOR | 0 |
| Écarts MINOR | 0 |
| Écarts INFO | 0 |

---

## Écarts constatés

Aucun écart détecté.

---

## Points positifs

- **Domain purity** : La couche `domain/` est totalement isolée. Aucune dépendance à FastAPI, aiosqlite, Pydantic ou infrastructure. Les modèles utilisent uniquement des dataclasses.
- **Ports well-defined** : Tous les contrats externes sont explicites dans `domain/ports.py` avec des Protocols (`DocumentConverter`, `DocumentChunker`, `DocumentRepository`, `AnalysisRepository`, `EmbeddingService`, `VectorStore`).
- **Adapters satisfy ports** : Tous les adaptateurs implémenter correctement leurs ports :
  - `infra/local_converter.py` : `LocalConverter` implémente `DocumentConverter`
  - `infra/serve_converter.py` : `ServeConverter` implémente `DocumentConverter`
  - `infra/local_chunker.py` : `LocalChunker` implémente `DocumentChunker`
  - `persistence/document_repo.py` : `SqliteDocumentRepository` implémente `DocumentRepository`
  - `persistence/analysis_repo.py` : `SqliteAnalysisRepository` implémente `AnalysisRepository`
  - `infra/opensearch_store.py` : `OpenSearchStore` implémente `VectorStore`
  - `infra/embedding_client.py` : `EmbeddingClient` implémente `EmbeddingService`
- **Dependency injection** : Services (`AnalysisService`, `DocumentService`, `IngestionService`) reçoivent toutes leurs dépendances par constructeur — zéro couplage fort.
- **Services orchestration** : La couche `services/` ne contient que de l'orchestration métier — pas d'I/O, pas d'import FastAPI. Imports : uniquement `domain/` et repos injectés.
- **Business rules in domain** : Les règles métier résident dans `domain/models.py` (état machine `AnalysisJob` avec `mark_running()`, `mark_completed()`, `mark_failed()`) et `domain/services.py` (fusion de résultats, classification des erreurs).
- **API layer decoupling** : Routes HTTP (`api/documents.py`, `api/analyses.py`) importent services, pas persistence/infra directement. Transformation camelCase centralisée dans `api/schemas.py`.
- **Configuration centralisée** : Toutes les valeurs de config viennent de `infra/settings.py`, construites via `Settings.from_env()` — zéro hardcoded en dur.
- **Clean main.py** : Entry point `main.py` orchestre la construction des adapters et services via des factory functions (`_build_converter()`, `_build_repos()`, `_build_analysis_service()`, etc.) — injection contrôlée.

---

## Verdict partiel : GO
