# Synthese d'audit — Release 0.5.0

**Date** : 2026-04-28
**Branche** : `release/0.5.0`
**Commit audite** : `b2e0af3`
**Auditeur** : claude-code

---

## Tableau de bord

| #  | Audit                | Score   | CRIT | MAJ | MIN | INFO | Verdict          |
|----|----------------------|---------|------|-----|-----|------|------------------|
| 01 | Clean Architecture   | 100     | 0    | 0   | 0   | 0    | GO               |
| 02 | DDD                  | 91      | 0    | 1   | 1   | 0    | GO               |
| 03 | Clean Code           | 83      | 0    | 0   | 3   | 0    | GO               |
| 04 | KISS                 | 87.5    | 0    | 0   | 1   | 2    | GO               |
| 05 | DRY                  | 71      | 0    | 2   | 1   | 2    | GO CONDITIONNEL  |
| 06 | SOLID                | 85      | 0    | 1   | 1   | 0    | GO               |
| 07 | Decouplage           | 86      | 0    | 1   | 1   | 0    | GO CONDITIONNEL  |
| 08 | Securite             | 91      | 0    | 2   | 0   | 1    | GO CONDITIONNEL  |
| 09 | Tests                | 94      | 0    | 1   | 0   | 0    | GO               |
| 10 | CI / Build           | 91      | 0    | 1   | 0   | 0    | GO CONDITIONNEL  |
| 11 | Documentation        | **44**  | **1**| 2   | 0   | 0    | **NO-GO**        |
| 12 | Performance          | 86.67   | 0    | 1   | 1   | 1    | GO CONDITIONNEL  |

**Score global (moyenne simple)** : **84.2 / 100**
**Ecarts CRITICAL totaux** : **1**
**Ecarts MAJOR totaux** : **12**
**Ecarts MINOR totaux** : 8
**Ecarts INFO totaux** : 6

---

## Ecarts CRITICAL (tous audits confondus)

1. **[11] CHANGELOG.md sans section `[0.5.0]`** — `CHANGELOG.md:7`
   La derniere section listee est `## [0.4.0] - 2026-04-13`. Aucune entree `[Unreleased]` ni `[0.5.0]`. Tagger 0.5.0 depuis ce HEAD livrerait un changelog mensonger qui omet les nouveautes de la release (reasoning-trace viewer, Neo4j graph storage, RAG endpoints, feature flags). **Bloquant absolu** par regle master §3.

---

## Top blockers (poids 3 / poids 2)

### Bloquant (poids 3)

- **[11] CHANGELOG sans section 0.5.0** — `CHANGELOG.md:7`
  Ajouter `## [0.5.0] - 2026-04-28` avec sous-sections `Added` / `Changed` / `Fixed` listant les changements depuis 0.4.0.

### Majeurs (poids 2) — a remediar pour passer a GO

- **[11] `frontend/package.json` toujours a `0.4.0`** — `frontend/package.json:3`
  Bumper a `"version": "0.5.0"`.
- **[11] Modifications de la release 0.5.0 non documentees** — `CHANGELOG.md`
  Resolu en meme temps que le CRIT.
- **[08] Mot de passe Neo4j par defaut `"changeme"`** — `document-parser/infra/settings.py:30,133`
  Forcer la lecture d'une variable d'environnement, supprimer le defaut, faire echouer le boot si absent en prod.
- **[08] OpenSearch security plugin desactive** — `docker-compose.yml:26`
  `DISABLE_SECURITY_PLUGIN=true` doit etre off pour tout deploiement non-dev ; documenter explicitement le perimetre.
- **[05] URL d'API hardcodee en frontend** — `frontend/src/features/settings/store.ts:23`
  Centraliser dans une constante `API_BASE_URL` lue depuis `import.meta.env`.
- **[05] Cles localStorage en clair, dispersees** — `frontend/src/features/settings/store.ts:24-27`
  Centraliser dans une enum/objet `STORAGE_KEYS`.
- **[02] Ubiquitous language "job" vs "analysis"** — `document-parser/api/ingestion.py:49-67`
  Aligner le vocabulaire HTTP sur le langage du domaine.
- **[06] LSP — `isinstance()` sur adaptateur** — `document-parser/services/analysis_service.py:356`
  Supprimer le check de type concret ou exposer la capacite via le port.
- **[07] Couplage inter-feature dans les tests** — `frontend/src/features/history/navigation.test.ts:30-31,67,82-83,143-144,169-170,188`
  Stubber les stores via injection au lieu d'imports directs.
- **[09] Assertions vagues `assert X is not None`** — 18 occurrences en backend
  Ajouter une assertion sur la valeur attendue, pas seulement sur la presence.
- **[10] Ruff UP038 — syntaxe `isinstance()` union** — `document-parser/infra/docling_tree.py:101`
  Appliquer la suggestion pyupgrade.
- **[12] I/O synchrone dans endpoint async** — `document-parser/api/documents.py:115-116`
  Wrapper l'acces fichier dans `asyncio.to_thread(...)` pour ne pas bloquer la loop FastAPI.

---

## Quick wins (poids 1 — ameliorations rapides)

- **[03] Trois fichiers Vue > 300 lignes** — `frontend/src/views/StudioPage.vue` (~1450L), `frontend/src/.../ChunkPanel.vue` (~801L), `frontend/src/.../ResultTabs.vue` (~690L). Extraire des sous-composants.
- **[03] Fonctions > 30 lignes** (3 cas) et **fonctions > 4 parametres** (4 cas). Decoupage local.
- **[04] Wrapper trivial `_to_response`** — utiliser `Pydantic.model_validate()` directement.
- **[04] Accessors redondants dans `DocumentService`**.
- **[05] Magic string isolee** — `document-parser/api/schemas.py:49`.
- **[12] Polling avec setInterval/setTimeout imbriques** — `frontend/src/features/settings/store.ts:27-39` et store analysis.

---

## Verdict final : **NO-GO**

**Justification** : 1 ecart CRITICAL non resolu dans l'audit 11 (Documentation) → regle absolue du master.md §3 : `tout ecart [CRIT] non resolu = NO-GO quel que soit le score`.

Bien que le score global (84.2/100) soit confortablement au-dessus du seuil GO et que 11 audits sur 12 soient au moins en GO CONDITIONNEL, le release 0.5.0 **ne peut pas etre tague** dans cet etat.

### Conditions pour passer a GO

**Bloquant absolu** (1 action) :
1. Ajouter la section `## [0.5.0] - 2026-04-28` dans `CHANGELOG.md` avec `Added` / `Changed` / `Fixed`.

**Pour passer de GO CONDITIONNEL a GO** (4 actions, ~30 min) :
2. Bumper `frontend/package.json` a `0.5.0`.
3. Remplacer `"changeme"` par lecture d'env var obligatoire (`document-parser/infra/settings.py`).
4. Documenter / corriger la desactivation du security plugin OpenSearch (`docker-compose.yml`).
5. Centraliser l'URL d'API et les cles localStorage du frontend (`frontend/src/features/settings/store.ts`).

**Recommandation** : apres remediation des 5 points ci-dessus, re-auditer **uniquement** les audits 11, 08 et 05 (commande : `Re-audite uniquement les ecarts CRITICAL et MAJOR du rapport docs/audit/reports/release-0.5.0/summary.md`). Les autres MAJ peuvent etre planifies pour 0.5.1 sans bloquer le tag.
