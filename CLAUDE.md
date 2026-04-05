# Docling Studio

Plateforme d'analyse documentaire visuelle : upload de PDFs, extraction (texte, tableaux, images, formules, bounding boxes), export Markdown/HTML.

## Stack

- **Frontend** : Vue 3, TypeScript (strict), Vite, Pinia, Vitest
- **Backend** : FastAPI, Python 3.12+, Docling 2.x, aiosqlite (SQLite), pytest
- **Infra** : Docker Compose, Nginx (reverse proxy), GitHub Actions CI/CD

## Structure

```
frontend/          # Vue 3 SPA (feature-based: features/{name}/api/, store/, ui/)
document-parser/   # FastAPI backend (Clean Architecture: domain/, api/, persistence/, infra/, services/)
docs/              # MkDocs documentation
```

## Commandes

### Backend (depuis `document-parser/`)

```bash
ruff check .              # Lint
ruff check . --fix        # Lint + auto-fix
ruff format .             # Format
pytest tests/ -v          # Tests (199 tests, asyncio_mode=auto)
uvicorn main:app --reload --port 8000  # Dev server
```

### Frontend (depuis `frontend/`)

```bash
npm run lint              # ESLint
npm run lint:fix          # ESLint + auto-fix
npm run format            # Prettier
npm run format:check      # Prettier check
npm run test:run          # Vitest (129 tests)
npm run type-check        # vue-tsc --noEmit
npm run build             # Type-check + build
npm run dev               # Dev server port 3000
```

### Docker

```bash
docker compose up         # Dev (frontend + backend)
```

## Git

- **Ne jamais push** : Claude ne doit jamais exécuter `git push`.
- **Pas de co-auteur** : aucune mention de Claude dans les commits (pas de `Co-Authored-By`, pas de signature).
- **Branches** : `feature/*`, `fix/*`, `release/*`. PR vers `main`. Ne jamais empiler de branches sur des branches feature — toujours partir de `main`.
- **Commits** : messages concis en anglais, verbe impératif (`Fix`, `Add`, `Refactor`), orientés "why" plutôt que "what".

## Validation pipeline

**Obligatoire avant de considérer toute tâche terminée.** Exécuter dans l'ordre :

### Backend (depuis `document-parser/`)

```bash
cd document-parser
.venv/bin/ruff check . --fix        # 1. Lint + auto-fix
.venv/bin/ruff format .             # 2. Format
.venv/bin/ruff check .              # 3. Vérifier zéro violation restante
.venv/bin/ruff format --check .     # 4. Vérifier zéro diff de format
.venv/bin/pytest tests/ -v          # 5. Tous les tests passent
```

### Frontend (depuis `frontend/`)

```bash
cd frontend
PATH="/usr/local/bin:$PATH" npm run lint:fix       # 1. ESLint auto-fix
PATH="/usr/local/bin:$PATH" npm run format         # 2. Prettier format
PATH="/usr/local/bin:$PATH" npm run lint           # 3. Vérifier zéro violation restante
PATH="/usr/local/bin:$PATH" npm run format:check   # 4. Vérifier zéro diff de format
PATH="/usr/local/bin:$PATH" npm run type-check     # 5. vue-tsc --noEmit
PATH="/usr/local/bin:$PATH" npm run test:run       # 6. Tous les tests passent
```

### Critères de validation

- **Zéro violation** de lint ou format sur les deux projets.
- **Tous les tests passent** — aucun skip, aucun xfail non justifié.
- **Tout nouveau code a des tests** — pas de code non couvert dans un commit.
- Si un fichier a été modifié, relancer la pipeline complète du projet concerné (backend, frontend, ou les deux).

## Conventions

- **API contracts** : camelCase (Pydantic `alias_generator` + frontend). snake_case pour le Python interne.
- **Frontend** : architecture feature-based, path alias `@/` = `src/`, tests colocalisés (`*.test.ts`).
- **Backend** : Clean Architecture — domain pur (pas de dépendances externes), repository pattern, ports abstraits, converters pluggables (local/remote). Imports first-party : `api`, `domain`, `persistence`, `services`.
- **Linting** : Ruff (backend, line-length 100), ESLint 9 flat config + Prettier (frontend, 100 chars, sans semicolons, single quotes).
- **Tests** : toujours lancer les tests et le lint avant de considérer une tâche terminée (voir section Validation pipeline ci-dessus).
- **Pas de fichiers inutiles** : préférer modifier l'existant plutôt que créer de nouveaux fichiers.
- **Voir aussi** : `CONTRIBUTING.md` pour le guide de contribution complet.
