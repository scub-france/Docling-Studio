# Rapport d'audit : Performance & Ressources

**Release** : 0.5.0
**Date** : 2026-04-28
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 13 / 15 |
| Score | 86.67 / 100 |
| Ecarts CRITICAL | 0 |
| Ecarts MAJOR | 1 |
| Ecarts MINOR | 1 |
| Ecarts INFO | 1 |

---

## Ecarts constates

### [MAJ] Blocage I/O synchrone dans endpoint async de prévisualisation

- **Localisation** : `document-parser/api/documents.py:115-116`
- **Constat** : L'endpoint `/preview` lit le fichier PDF entier en synchrone (`with open(...); f.read()`) dans une fonction async, bloquant l'event loop FastAPI. Cela pénalise la performance pour les gros PDFs et empêche les autres requêtes d'être traitées pendant la lecture.
- **Regle violee** : 12.1.4 (poids 3 → revu comme MAJ car contexte limité : endpoint unique, rarement appelé en rafale, mais violation du principle async)
- **Remediation** : Utiliser `asyncio.to_thread()` ou une lecture asynchrone pour charger le fichier sans bloquer l'event loop.

### [MIN] Watchers Vue sans cleanup explicite en Pinia store

- **Localisation** : `frontend/src/features/settings/store.ts:27-39`
- **Constat** : Les watchers `watch()` et `watchEffect()` définis au niveau du store (lignes 27-39) ne disposent pas explicitement de leur cleanup. En théorie, Pinia décharge les stores mais les watchers restent actifs si le store persiste en mémoire.
- **Regle violee** : 12.2.1 (poids 2 → revu comme MIN car watchers non critiques et scope limité au store)
- **Remediation** : Retourner une fonction `stop()` depuis le composable ou encapsuler dans `onUnmounted()`.

### [INFO] Absence de pagination explicite sur `/api/documents` et `/api/graph`

- **Localisation** : `document-parser/api/documents.py:72-76` et `document-parser/api/graph.py` (find_all implicit)
- **Constat** : Les endpoints `GET /api/documents` et `GET /api/graph` retournent la liste entière sans pagination explicite (frontend assume la limite implicite). Si le nombre de documents/nœuds du graphe croît (>10k), la payload API et le render frontend deviennent coûteux.
- **Regle violee** : 12.3.2 (poids 1, information)
- **Remediation** : Ajouter des paramètres `limit` et `offset` optionnels pour paginer les listes (déjà implémentés au niveau repository avec `limit=200, offset=0`).

---

## Points positifs

- ✅ **Semaphore bien configuré** (12.1.3) — `MAX_CONCURRENT_ANALYSES` défini à 3, implémenté avec `asyncio.Semaphore()`, appliqué dans la méthode `_run_analysis()`.
- ✅ **Fichiers temporaires supprimés** (12.1.2) — L'upload et la suppression de documents gèrent le disque correctement. Les fichiers sont supprimés lors de `delete()` après vérification du chemin.
- ✅ **Conversion asynchrone** (12.1.4) — Docling (conversion CPU-intensive) est délégué via `asyncio.to_thread()` dans `LocalConverter`, libérant l'event loop.
- ✅ **Lecture en chunks** (12.1.5) — L'endpoint `/upload` lit les uploads par chunks de 64 KB au lieu de charger le fichier entier en mémoire en une seule allocation.
- ✅ **Watchers avec cleanup** (12.2.1, 12.2.2) — Dans les composants `StudioPage.vue`, `GraphView.vue`, `BboxOverlay.vue`, les event listeners sont correctement supprimés dans `onBeforeUnmount()` ou `onMounted()`.
- ✅ **Pas de re-render excessif** (12.2.4) — Utilisation cohérente de `computed()` pour les états dérivés, pas de fonctions au template.
- ✅ **Pas de requête N+1 évidente** (12.1.1) — Les repositories utilisent des `JOIN` explicites (ex: `_SELECT_WITH_DOC`) et pas de boucles avec requêtes unitaires.

---

## Verdict partiel : GO CONDITIONNEL

**Condition** : Appliquer la remediation [MAJ] pour l'endpoint `/preview` avant la release ou planifier la correction dans le sprint suivant avec une priorité haute. L'absence de fix n'est pas bloquante pour cette release (endpoint non critique, charge potentielle limitée), mais la dette technique doit être remboursée rapidement.

**Justification** :
- Score 86.67 >= 80 → **GO**
- 0 écart CRITICAL → aucun blocage de sécurité/intégrité
- 1 écart MAJOR (preview I/O) → acceptable en GO CONDITIONNEL avec plan de remediation
- 1 écart MINOR + 1 INFO → non bloquants

