# Audit Master — Release Branch Quality Gate

Referentiel central d'audit qualite pour les branches `release/X.Y.Z` de Docling Studio.

Ce document est le **chef d'orchestre** : il definit les regles, commandite les audits unitaires, et normalise les rapports.

---

## 1. Perimetre

L'audit s'execute sur une branche `release/X.Y.Z` **apres feature freeze**, avant le merge dans `main`.

**Cibles :**

| Cible | Chemin |
|-------|--------|
| Backend (Python/FastAPI) | `document-parser/` (hors `.venv/`, `__pycache__/`, `tests/`) |
| Frontend (Vue 3/TypeScript) | `frontend/src/` |
| Tests backend | `document-parser/tests/` |
| Tests frontend | `frontend/src/**/*.test.*` |
| Tests e2e | `e2e/` |
| Infrastructure | `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `.github/` |

---

## 2. Niveaux de criticite

Chaque ecart trouve lors d'un audit est classe selon ces 4 niveaux :

| Niveau | Tag | Description | Impact sur le GO/NO-GO |
|--------|-----|-------------|------------------------|
| **CRITICAL** | `[CRIT]` | Violation bloquante — faille de securite, corruption de donnees, violation d'architecture majeure | **Bloquant** — le release ne peut pas partir |
| **MAJOR** | `[MAJ]` | Violation significative — couplage fort, dette technique importante, test manquant sur un chemin critique | Bloquant si > 3 ecarts MAJOR non resolus |
| **MINOR** | `[MIN]` | Ecart de qualite — nommage, taille de fichier, duplication legere | Non bloquant — a corriger dans le prochain cycle |
| **INFO** | `[INFO]` | Observation, suggestion d'amelioration, bonne pratique non respectee mais sans risque | Non bloquant — informatif |

---

## 3. Bareme de compliance

Chaque audit unitaire produit une **note de compliance sur 100**.

### Calcul

Chaque item de checklist a un **poids** defini dans la fiche d'audit :

| Poids | Signification |
|-------|---------------|
| 3 | Critique — violation = ecart CRITICAL |
| 2 | Important — violation = ecart MAJOR |
| 1 | Standard — violation = ecart MINOR |

**Formule :**

```
score = (somme des poids des items conformes / somme totale des poids) * 100
```

### Seuils de decision

| Score | Verdict | Action |
|-------|---------|--------|
| >= 80 | **GO** | Release autorisee |
| 60 - 79 | **GO CONDITIONNEL** | Release autorisee si 0 CRITICAL, plan de remediation pour les MAJOR |
| < 60 | **NO-GO** | Release bloquee — corriger et re-auditer |

**Regle absolue** : tout ecart `[CRIT]` non resolu = **NO-GO** quel que soit le score.

---

## 4. Liste des audits

Les audits sont executes dans l'ordre ci-dessous. Chacun est une fiche autonome dans `audits/`.

| # | Audit | Fichier | Focus |
|---|-------|---------|-------|
| 01 | Hexagonal Architecture | [01-clean-architecture.md](audits/01-clean-architecture.md) | Ports & adapters, respect des couches, flux de dependances |
| 02 | DDD | [02-ddd.md](audits/02-ddd.md) | Bounded contexts, entites, value objects, ubiquitous language |
| 03 | Clean Code | [03-clean-code.md](audits/03-clean-code.md) | Nommage, taille, lisibilite |
| 04 | KISS | [04-kiss.md](audits/04-kiss.md) | Simplicite, pas de sur-ingenierie |
| 05 | DRY | [05-dry.md](audits/05-dry.md) | Duplication, factorisation |
| 06 | SOLID | [06-solid.md](audits/06-solid.md) | 5 principes SOLID |
| 07 | Decouplage | [07-decoupling.md](audits/07-decoupling.md) | Front/back, inter-features, contrats |
| 08 | Securite | [08-security.md](audits/08-security.md) | OWASP, secrets, injection, CORS |
| 09 | Tests | [09-tests.md](audits/09-tests.md) | Couverture, qualite, e2e |
| 10 | CI / Build | [10-ci-build.md](audits/10-ci-build.md) | Pipeline, Docker, health check |
| 11 | Documentation | [11-documentation.md](audits/11-documentation.md) | Changelog, version, TODOs |
| 12 | Performance | [12-performance.md](audits/12-performance.md) | N+1, memory, concurrence |

---

## 5. Format de rapport attendu

Chaque audit produit un rapport dans `reports/release-X.Y.Z/XX-nom.md` respectant ce format :

```markdown
# Rapport d'audit : [Nom de l'audit]

**Release** : X.Y.Z
**Date** : YYYY-MM-DD
**Auditeur** : [nom ou "claude-code"]

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | XX / YY |
| Score | XX / 100 |
| Ecarts CRITICAL | N |
| Ecarts MAJOR | N |
| Ecarts MINOR | N |
| Ecarts INFO | N |

---

## Ecarts constates

### [CRIT] Titre de l'ecart
- **Localisation** : `chemin/fichier.py:ligne`
- **Constat** : description factuelle
- **Regle violee** : reference a l'item de checklist
- **Remediation** : action corrective proposee

### [MAJ] Titre de l'ecart
...

### [MIN] Titre de l'ecart
...

### [INFO] Titre de l'ecart
...

---

## Points positifs

- ...

---

## Verdict partiel : GO / GO CONDITIONNEL / NO-GO
```

---

## 6. Rapport de synthese

Le fichier `reports/release-X.Y.Z/summary.md` consolide tous les audits :

```markdown
# Synthese d'audit — Release X.Y.Z

**Date** : YYYY-MM-DD
**Branche** : release/X.Y.Z

---

## Tableau de bord

| # | Audit | Score | CRIT | MAJ | MIN | INFO | Verdict |
|---|-------|-------|------|-----|-----|------|---------|
| 01 | Hexagonal Architecture | XX | N | N | N | N | GO |
| 02 | DDD | XX | N | N | N | N | GO |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Score global** : XX / 100 (moyenne ponderee)
**Ecarts CRITICAL totaux** : N
**Ecarts MAJOR totaux** : N

---

## Ecarts CRITICAL (tous audits confondus)

1. [audit] description — fichier:ligne

---

## Verdict final : GO / GO CONDITIONNEL / NO-GO

Conditions (si GO CONDITIONNEL) :
- ...
```

---

## 7. Execution

### Lancer un audit complet

```
Audite la branche release/X.Y.Z en suivant docs/audit/master.md
```

### Lancer un audit unitaire

```
Execute l'audit docs/audit/audits/02-ddd.md sur la branche courante
```

### Re-auditer apres correction

```
Re-audite uniquement les ecarts CRITICAL et MAJOR du rapport docs/audit/reports/release-X.Y.Z/summary.md
```
