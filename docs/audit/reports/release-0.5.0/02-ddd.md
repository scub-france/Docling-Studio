# Rapport d'audit : Domain-Driven Design (DDD)

**Release** : 0.5.0  
**Date** : 2026-04-28  
**Auditeur** : claude-code

---

## Score de compliance

| Métrique | Valeur |
|----------|--------|
| Items conformes | 20 / 22 |
| Score | 91 / 100 |
| Écarts CRITICAL | 0 |
| Écarts MAJOR | 1 |
| Écarts MINOR | 1 |
| Écarts INFO | 0 |

---

## Écarts constatés

### [MAJ] Ubiquitous language — "job" vs "analysis" dans l'API HTTP

- **Localisation** : `document-parser/api/ingestion.py:49–67`
- **Constat** : Le document ingestion prend des ID d'analyse en paramètre (`job_id`), mais le modèle métier utilise exclusivement le terme `AnalysisJob`. Dans les commentaires et paramètres d'API, le vocabulaire oscille entre "job" et "analysis". Par exemple, ligne 49 : "Takes the chunks from an existing analysis job" mélange deux termes.
- **Règle violée** : 2.3.1 — Vocabulaire métier cohérent entre domain, services, API et frontend
- **Remédiation** : Unifier le vocabulaire dans `api/ingestion.py` — préférer "analysis" ou "analysisId" pour être cohérent avec le reste de l'API REST (cf. `/api/analyses/{id}`). Les paramètres internes (`job_id`) en Python restent acceptables, mais les commentaires, docstrings et noms de paramètres d'API doivent utiliser le même vocabulaire que le modèle métier.

### [MIN] AnalysisJob mutable après création — pas de garantie d'invariants au-delà du service

- **Localisation** : `document-parser/domain/models.py:37–99`
- **Constat** : `AnalysisJob` est un dataclass mutable (non gelée). Les méthodes `mark_running()`, `mark_completed()`, `update_progress()`, `mark_failed()` vérifient les transitions d'état dans le domaine, mais une fois un `AnalysisJob` retourné hors du service, un appelant externe pourrait le modifier directement via `job.status = ...` ou `job.content_markdown = ...`. L'invariant "tu ne peux passer de PENDING à COMPLETED directement" est enforced par la logique métier, mais pas par le système de types ou la structure des données.
- **Règle violée** : 2.4.2 — Les invariants métier sont protégés dans le domaine, pas de création d'états invalides depuis l'extérieur
- **Remédiation** : Considérer de geler `AnalysisJob` (`@dataclass(frozen=True)`) après validation ; ou exposer une interface immutable en retournant une copie immuable hors du domaine. Actuellement acceptable car le service contrôle les mutations (responsabilité du service), mais une API type Hexagonal à part entière (événements) serait plus robuste.

---

## Points positifs

- **Bounded contexts clairs** (2.1.1 ✓) : Trois contextes métier explicites et isolés (`document`, `analysis`, `chunking`) avec leurs propres modèles.
- **Pas de god objects** (2.1.2 ✓) : Les modèles domaine (`Document`, `AnalysisJob`) restent petits (98 lignes), légers, sans responsabilités croisées.
- **Séparation des responsabilités via ports** (2.1.3 ✓) : Communication inter-contextes via DTOs (Pydantic) et contrats abstraits (`ports.py`), pas d'imports croisés de modèles internes.
- **Value objects correctement immutables** (2.2.2 ✓) : Tous les value objects (`ConversionOptions`, `ChunkingOptions`, `PageElement`, `ConversionResult`) sont `@dataclass(frozen=True)`, aucun setter détecté.
- **Value objects sans persistance** (2.2.3 ✓) : Aucune méthode `save()`, `update()`, `delete()` sur les value objects.
- **Entités avec identité et comportement** (2.2.1, 2.2.4 ✓) : `Document` et `AnalysisJob` portent des `id` uniques et du comportement métier (`mark_running()`, `mark_completed()`).
- **Anti-corruption layer efficace** (2.5.2–2.5.3 ✓) : Les adaptateurs infrastructure (`local_converter.py`, `serve_converter.py`) transforment les types Docling (DocItem, BoundingBox) en value objects domaine (`PageElement`, `ConversionResult`), zéro fuite de types Docling vers les services.
- **Repositories manipulent des entités domaine** (2.5.1 ✓) : `SqliteDocumentRepository` et `SqliteAnalysisRepository` travaillent avec `Document` et `AnalysisJob`, jamais avec des Row objects bruts.
- **Statuts métier explicites** (2.3.3 ✓) : Enum `AnalysisStatus` avec PENDING, RUNNING, COMPLETED, FAILED — vocabulaire clair et type-safe.
- **Ubiquitous language dominant cohérent** (2.3.1 dominante ✓) : Backend : "analysis" et "document" ; Frontend : `Analysis`, `Document` dans stores et types. 99 % de cohérence sur l'ensemble.
- **Agrégats avec racines explicites** (2.4.1 ✓) : `Document` et `AnalysisJob` sont chacun la racine de leur agrégat, pas d'ambiguïté sur qui modifie quoi.
- **Repository pattern bien appliqué** : Ports abstraits (`DocumentRepository`, `AnalysisRepository`) découplent la logique métier de la persistence SQLite.
- **Pas de dépendances Docling dans services** (2.5.3 ✓) : `grep` confirme zéro `from docling` ou `import docling` dans `services/`.

---

## Verdict partiel : GO

**Justification** : 
- Score 91/100 (>= 80) ✓
- 0 écarts CRITICAL ✓
- 1 seul écart MAJOR (nommage/ubiquitous language mineure) — corrigeable en post-release
- 1 écart MINOR (immutabilité additionnelle, amélioration plutôt que violation)

L'architecture DDD est bien implantée : bounded contexts clairs, entités et value objects bien séparés, anti-corruption layer efficace, invariants maintenus. Les deux écarts sont de faible criticité et ne bloquent pas la release.

**Conditions pour GO** : 
- Les écarts MAJOR et MINOR sont non-bloquants en 0.5.0.
- Recommandation : inclure la remédiation de 2.3.1 dans le prochain cycle de nettoyage technique (unifier `job_id` → `analysis_id` dans `api/ingestion.py`).
