# Audit 01 — Hexagonal Architecture (ports & adapters)

**Objectif** : verifier que le backend respecte le pattern hexagonal (ports dans `domain/ports.py`, adaptateurs dans `infra/`), le flux de dependances strict `api -> services -> domain`, et que chaque couche a une responsabilite claire.

**Cible** : `document-parser/` (hors `.venv/`, `__pycache__/`, `tests/`)

---

## Checklist

### 1.1 Domain (couche pure)

| # | Item | Poids |
|---|------|-------|
| 1.1.1 | `domain/` n'importe ni FastAPI, ni aiosqlite, ni aucune lib infra | 3 |
| 1.1.2 | Les modeles, value objects et ports ne font aucun I/O (file, HTTP, DB) | 3 |
| 1.1.3 | Toute interaction avec l'exterieur passe par un protocole dans `domain/ports.py` | 3 |
| 1.1.4 | Pas de Pydantic dans domain — le domain utilise des dataclasses | 2 |

### 1.2 Services (orchestration)

| # | Item | Poids |
|---|------|-------|
| 1.2.1 | `services/` n'importe jamais `fastapi`, `Request`, `Response`, `Depends` | 3 |
| 1.2.2 | Les services appellent les repos, jamais de requetes SQL directes | 3 |
| 1.2.3 | Les regles metier vivent dans `domain/`, pas dans les services | 2 |
| 1.2.4 | Les services recoivent leurs dependances par injection, pas par import direct de concretions | 2 |

### 1.3 API (couche HTTP)

| # | Item | Poids |
|---|------|-------|
| 1.3.1 | Les routes n'importent pas `persistence/` directement | 3 |
| 1.3.2 | Les transformations camelCase/snake_case restent dans `api/schemas.py` | 1 |
| 1.3.3 | Les endpoints delegent toute la logique aux services | 2 |

### 1.4 Infra (adaptateurs)

| # | Item | Poids |
|---|------|-------|
| 1.4.1 | Chaque adaptateur dans `infra/` implemente un protocole de `domain/ports.py` | 3 |
| 1.4.2 | Les valeurs de config viennent de `infra/settings.py`, pas de constantes en dur | 2 |

---

## Commandes de verification

```bash
# 1.1.1 — Domain ne doit importer aucune lib infra
grep -rn "from fastapi\|from aiosqlite\|from pydantic\|import fastapi\|import aiosqlite" document-parser/domain/

# 1.2.1 — Services ne doivent pas importer FastAPI
grep -rn "from fastapi\|import fastapi" document-parser/services/

# 1.3.1 — API ne doit pas importer persistence
grep -rn "from persistence\|import persistence" document-parser/api/

# 1.4.2 — Constantes en dur dans infra (hors settings)
grep -rn "= ['\"]http\|= [0-9]\{4,\}" document-parser/infra/ --include="*.py" | grep -v settings.py
```

---

## Regles de notation

- Tout item de poids 3 non conforme = ecart `[CRIT]`
- Tout item de poids 2 non conforme = ecart `[MAJ]`
- Tout item de poids 1 non conforme = ecart `[MIN]`
