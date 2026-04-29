# Rapport d'audit : Decouplage

**Release** : 0.5.0
**Date** : 2026-04-28
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 13 / 15 |
| Score | 86 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 1 |
| Ecarts MINOR | 1 |
| Ecarts INFO | 0 |

---

## Ecarts constates

### [MAJ] Inter-store coupling in history feature test

- **Localisation** : `frontend/src/features/history/navigation.test.ts:30-31, 67, 82-83, 143-144, 169-170, 188`
- **Constat** : Le test `navigation.test.ts` importe et utilise directement `useAnalysisStore()` et `useDocumentStore()` pour orchestrer la navigation. Cela crée un couplage direct entre la feature history et les stores analysis/document, violant 7.2.2.
- **Regle violee** : 7.2.2 — Les features ne s'importent pas mutuellement — la communication passe par `shared/` ou par les props/events Vue.
- **Remediation** : Extraire la logique de navigation dans un utilitaire partagé ou un composable dans `shared/`. Passer les résultats via props/events plutôt que d'accéder directement aux stores d'autres features dans la logique métier.

### [MIN] Frontend API client lacks explicit mock layer support

- **Localisation** : `frontend/src/features/{analysis,document,chunking,search}/api.ts` — aucun pattern d'injection de mock ou de stub
- **Constat** : Les fichiers `api.ts` utilisent `apiFetch` directement sans interface abstraite. Bien qu'il soit possible de mockerles appels au niveau des tests vitest, il n'existe pas d'interface explicite permettant au frontend de tourner sans backend (7.1.3).
- **Regle violee** : 7.1.3 — Le frontend peut tourner avec un mock du backend (les appels API sont isoles dans des fichiers `api.ts` par feature).
- **Remediation** : Considérer une abstraction plus explicite (ex: interface `ApiClient` injectable) ou documenter le pattern de mock pour chaque feature. Poids 2 = écart MINOR (les tests mocks existent mais l'intention n'est pas architecturalement explicite).

---

## Points positifs

- ✓ **Decouplage Frontend/Backend solide** : Aucun import croise, contrat API basé sur REST, types TypeScript alignés avec Pydantic via `_to_camel` (schemas.py). Frontend utilise `apiFetch` (shared/api/http.ts) comme couche unique.
- ✓ **Hexagonal Architecture Backend** : Ports dans `domain/ports.py` définis avec types du domaine (ConversionResult, ChunkResult, etc.). Services importent uniquement `domain.ports` et `domain.value_objects`, zéro fuite de types docling.*. Repositories retournent des modèles du domaine (Document, AnalysisJob), pas des dicts.
- ✓ **Schemas API fortement typés** : Tous les DTOs dans `api/schemas.py` utilisent Pydantic BaseModel strictement (pas de `dict` ou `Any`). Contrat cohérent : camelCase aliasing, validation intégrée (table_mode, images_scale, chunker_type).
- ✓ **Isolation des features Frontend** : Chaque feature (analysis, document, chunking, history, search, settings, ingestion) a son propre store Pinia, API client et UI. Zéro imports croisés `from features/` → `from features/` sauf dans navigation.test.ts.
- ✓ **Infrastructure Adapter Boundary** : `infra/local_converter.py` importe Docling (DoclingConverter, CodeItem, etc.) mais retourne uniquement `ConversionResult` (domaine). Services ne voient jamais les types docling.
- ✓ **Configuration d'infra propre** : `docker-compose.yml` et `nginx.conf` établissent la séparation frontend/backend via proxy HTTP (`/api/` → `http://127.0.0.1:8000`). CORS déclaré explicitement.

---

## Verdict partiel : GO CONDITIONNEL

**Conditions** :
1. Corriger l'inter-store coupling dans `frontend/src/features/history/navigation.test.ts` (MAJ).
2. Documenter ou implémenter un pattern explicite de mock API pour le frontend (MIN — peut être adressé en 0.5.1).

**Score 86/100** : Satisfait >= 80 (GO). Un seul écart MAJOR, zéro CRITICAL. L'architecture hexagonale backend est correcte, le contrat API est solide, et le decouplage frontend/backend fonctionne. Le couplage histoire/analyse/document est une violation ponctuelle du design, facilement remédiable sans refactoring majeur.
