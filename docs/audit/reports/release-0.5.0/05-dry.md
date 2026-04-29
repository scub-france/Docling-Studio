# Rapport d'audit : DRY (Don't Repeat Yourself)

**Release** : 0.5.0
**Date** : 2026-04-28
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 5 / 7 |
| Score | 71 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 2 |
| Ecarts MINOR | 1 |
| Ecarts INFO | 2 |

---

## Ecarts constates

### [MAJ] Magic API URL hardcodé en frontend

- **Localisation** : `frontend/src/features/settings/store.ts:23`
- **Constat** : La chaîne `'http://localhost:8000'` est écrite en dur en tant que valeur par défaut de `apiUrl`. Aucune centralization dans un fichier de configuration partagé.
- **Regle violee** : Item 5.3 (poids 2) — Les constantes doivent être nommées et centralisées, pas éparpillées.
- **Remediation** : Créer `frontend/src/shared/config.ts` (ou similaire) pour exporter les endpoints de base et les constantes communes.

### [MAJ] Magic strings localStorage non centralisées en frontend

- **Localisation** : `frontend/src/features/settings/store.ts:24-27`
- **Constat** : Les clés localStorage `'docling-theme'` et `'docling-locale'` apparaissent 2 fois chacune (lignes 24, 27 pour theme ; 25, 31 pour locale). Ces chaînes ne sont pas extraites en constantes nommées.
- **Regle violee** : Item 5.3 (poids 2) — Les magic strings doivent être nommées et centralisées.
- **Remediation** : Créer des constantes nommées (e.g., `STORAGE_KEY_THEME = 'docling-theme'`) dans `frontend/src/shared/appConfig.ts` ou un nouveau `frontend/src/shared/constants.ts`.

### [MIN] Magic string "uploaded" non centralisé en backend

- **Localisation** : `document-parser/api/schemas.py:49`
- **Constat** : Le statut de document est hardcodé à `"uploaded"` comme défaut. Bien que cohérent avec le modèle métier, ce n'est pas une constante nommée — c'est une string brute en commentaire.
- **Regle violee** : Item 5.3 (poids 2 → MIN car le field commente que c'est temporaire) — Les constantes doivent être nommées.
- **Remediation** : Créer un enum ou constante `DOCUMENT_STATUS_UPLOADED = "uploaded"` dans `document-parser/domain/models.py` (déjà utilisé pour AnalysisStatus).

### [INFO] Validation de `table_mode` et `chunker_type` répétée

- **Localisation** : `document-parser/api/schemas.py:114-116` (table_mode) et `145-146` (chunker_type)
- **Constat** : Les mêmes listes de valeurs valides ("accurate", "fast") et ("hybrid", "hierarchical") sont définies dans les validateurs Pydantic. Ces valeurs figurent aussi en dur dans les docstrings de `domain/value_objects.py` (lignes 41, 67).
- **Regle violee** : Item 5.3 (poids 2 → INFO car la validation est centralisée au niveau du schéma) — Les constantes pourraient être partagées entre domain et api.
- **Remediation** : Créer un module `document-parser/domain/constants.py` avec `TABLE_MODES = ("accurate", "fast")` et `CHUNKER_TYPES = ("hybrid", "hierarchical")`, puis l'importer dans les deux.

### [INFO] Logique de polling dupliquée entre features

- **Localisation** : `frontend/src/features/analysis/store.ts` (ligne 67+) et `frontend/src/features/ingestion/store.ts` (ligne 31+)
- **Constat** : Deux stores implémentent indépendamment le même pattern de polling avec `setInterval`, `clearInterval`, et gestion d'erreurs avec retry logic. Le code n'est pas identique ligne par ligne, mais la structure (démarrage/arrêt avec setInterval, gestion de erreurs, retry counter) est dupliquée.
- **Regle violee** : Item 5.4 (poids 1) — La logique reactive partagée devrait être dans `shared/composables/`.
- **Remediation** : Extraire un composable réutilisable (e.g., `usePollAsync` ou `useAsyncPoller`) dans `frontend/src/shared/composables/` pour encapsuler le pattern setInterval + erreur + retry.

---

## Points positifs

- ✅ Centralisation réussie de la config HTTP : tous les appels `apiFetch` passent par `frontend/src/shared/api/http.ts` — aucun fetch() direct détecté.
- ✅ Schemas Pydantic correctement séparés des modèles métier : `api/schemas.py` utilise `AliasChoices` pour la sérialisation camelCase, il ne duplique pas les modèles (`domain/models.py` reste pur).
- ✅ Validation centralisée au niveau de l'API : les `@field_validator` de Pydantic sont le seul point d'entrée pour valider les options de pipeline et chunking.
- ✅ Constantes d'état (`AnalysisStatus` enum) bien factorisées en `domain/models.py` — aucune duplication de "PENDING", "RUNNING", "COMPLETED", "FAILED".
- ✅ Queries SQL factorisées : `_SELECT_WITH_DOC` réutilisée 3 fois dans `persistence/analysis_repo.py`.

---

## Verdict partiel : GO CONDITIONNEL

**Justification** :
- Score 71 / 100 (seuil: 80) → au-dessous de GO, mais aucun CRITICAL.
- 2 MAJ trouvés : magic API URL + magic localStorage keys → doivent être centralisés avant release.
- 1 MIN + 2 INFO pour amélioration future (pas bloquant immédiatement).

**Conditions pour GO** :
1. Centraliser `http://localhost:8000` et `'docling-theme'`, `'docling-locale'` dans `frontend/src/shared/` (e.g., `config.ts` ou `constants.ts`).
2. Exécuter la re-vérification après correction pour atteindre ≥ 80.

**Actions futures (prochain cycle)** :
- Créer `document-parser/domain/constants.py` pour les validations (table_mode, chunker_type).
- Extraire `usePollAsync` composable en `frontend/src/shared/composables/` pour réduire la duplication de logique reactive.
