# Rapport d'audit : Documentation & Changelog

**Release** : 0.5.0
**Date** : 2026-04-28
**Auditeur** : claude-code

---

## Score de compliance

| Metrique | Valeur |
|----------|--------|
| Items conformes | 5 / 9 |
| Score | **44 / 100** |
| Ecarts CRITICAL | 1 |
| Ecarts MAJOR | 2 |
| Ecarts MINOR | 0 |
| Ecarts INFO | 0 |

### Detail

| # | Item | Poids | Statut |
|---|------|-------|--------|
| 11.1.1 | `[Unreleased]` renommee en `[X.Y.Z] - YYYY-MM-DD` | 3 | **KO** |
| 11.1.2 | Modifications de la release listees | 2 | **KO** |
| 11.1.3 | Breaking changes identifies | 3 | OK |
| 11.1.4 | Format Keep a Changelog | 1 | OK |
| 11.2.1 | `package.json` a la bonne version | 2 | **KO** |
| 11.2.2 | Semantic Versioning | 2 | OK |
| 11.3.1 | Pas de TODO orphelin | 1 | OK |
| 11.3.2 | Pas de `console.log` de debug | 2 | OK |
| 11.3.3 | Pas de `print()` de debug | 2 | OK |

**Calcul** : poids conformes 3+1+2+2 = 8 / poids total 18 = 44.4 → 44.

---

## Ecarts constates

### [CRIT] CHANGELOG.md sans section `[0.5.0]`

- **Localisation** : `CHANGELOG.md:7`
- **Constat** : la derniere section est `## [0.4.0] - 2026-04-13`. Aucune section `[Unreleased]` ni `[0.5.0]` n'est presente. Pour une release nommee 0.5.0, la regle 11.1.1 (poids 3) exige une section `[0.5.0] - YYYY-MM-DD`.
- **Regle violee** : 11.1.1.
- **Impact** : aucune trace des nouveautes 0.5.0 (reasoning viewer, Neo4j integration, RAG endpoints). Un tag 0.5.0 cree depuis ce HEAD livrerait un changelog mensonger.
- **Remediation** : ajouter section `## [0.5.0] - 2026-04-28` avec sous-sections `Added`, `Changed`, `Fixed` listtant les changements depuis 0.4.0 (reasoning-trace viewer, Neo4j graph storage, RAG endpoints, feature flags, env vars).

### [MAJ] Modifications de la release 0.5.0 non documentees

- **Localisation** : `CHANGELOG.md`
- **Constat** : corollaire direct de l'ecart 11.1.1. Aucun bullet n'enumere les nouveautes de cette release (11.1.2, poids 2). Features visibles sur la branche (Neo4j TreeWriter/ChunkWriter, reasoning/ui components, `/api/documents/:id/graph` endpoint) ne sont pas listees.
- **Regle violee** : 11.1.2.
- **Remediation** : voir CRIT 11.1.1.

### [MAJ] `frontend/package.json` toujours a `0.4.0`

- **Localisation** : `frontend/package.json:3`
- **Constat** : `"version": "0.4.0"`. Pour une release 0.5.0, il faut bumper a `"version": "0.5.0"` (regle 11.2.1, poids 2).
- **Impact** : la version du frontend reste `0.4.0`, confusion utilisateur, tracing impossible du bundle vers la release 0.5.0.
- **Remediation** : bumper a `"version": "0.5.0"` avant le tag final.

---

## Points positifs

- **Zero `console.log`/`console.debug`** dans le code frontend. Les 2 occurrences de `console.warn` (store.ts:85, ReasoningPanel.vue:150) respectent la convention permise.
- **Zero `print()` de debug** dans le backend (hors tests).
- **Zero TODO/FIXME/HACK/XXX** dans le code productif.
- **Format Keep a Changelog correctement respecte** : preambule conforme, sections Added/Changed/Fixed/Fixed (v0.4.0), chronologie inverse.
- **Semantic Versioning suivi** : sequence 0.1.0 → 0.2.0 → 0.3.0 → 0.3.1 → 0.4.0 → (0.5.0 en attente) coherente.

---

## Verdict partiel : NO-GO

Score 44/100 < 60 (seuil minimum) et **1 ecart CRITICAL non resolu** (regle absolue du master : tout `[CRIT]` non resolu = NO-GO).

Le release 0.5.0 ne peut pas partir (ne peut pas etre taguee) tant que :

1. **CHANGELOG.md** n'enumere pas les changements sous `## [0.5.0] - YYYY-MM-DD`.
2. **frontend/package.json** n'est pas bumpe a `0.5.0`.

Recommendation : apres avoir resolu ces deux points, relancer l'audit 11.
