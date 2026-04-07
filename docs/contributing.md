# Contributing

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/Docling-Studio.git
   cd Docling-Studio
   ```
3. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Setup

=== "Backend (Python 3.12+)"

    ```bash
    cd document-parser
    python -m venv .venv && source .venv/bin/activate

    # Remote mode (lightweight — delegates to Docling Serve)
    pip install -r requirements.txt

    # Local mode (full — runs Docling in-process)
    pip install -r requirements-local.txt

    pip install ruff pytest pytest-asyncio httpx
    uvicorn main:app --reload --port 8000
    ```

=== "Frontend (Node 20+)"

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Code Quality

### Backend — Ruff

```bash
cd document-parser
ruff check .          # lint
ruff check . --fix    # auto-fix
ruff format .         # format
```

### Frontend — TypeScript + ESLint + Prettier

```bash
cd frontend
npm run type-check          # vue-tsc strict mode
npx eslint src/             # lint
npx prettier --check src/   # check formatting
npx prettier --write src/   # auto-format
```

## Running Tests

=== "Backend"

    ```bash
    cd document-parser
    pytest tests/ -v
    ```

=== "Frontend"

    ```bash
    cd frontend
    npm run test:run
    ```

All tests must pass before submitting a PR.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Add tests for new functionality
- Update documentation if behavior changes
- Ensure CI passes (lint + type-check + tests + build)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/scub-france/Docling-Studio/blob/main/LICENSE).
