# Contributing to Docling Studio

Thank you for your interest in contributing to Docling Studio! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Docling-Studio.git
   cd Docling-Studio
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Setup

### Backend (Python 3.12+)

```bash
cd document-parser
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest pytest-asyncio httpx  # dev tools
uvicorn main:app --reload --port 8000
```

### Frontend (Node 20+)

```bash
cd frontend
npm install
npm run dev
```

## Code Quality

### Backend — Ruff

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting Python code.

```bash
cd document-parser
ruff check .          # lint
ruff check . --fix    # lint with auto-fix
ruff format .         # format
```

### Frontend — TypeScript + ESLint + Prettier

```bash
cd frontend
npm run type-check          # type check (vue-tsc)
npx eslint src/             # lint
npx prettier --check src/   # check formatting
npx prettier --write src/   # auto-format
```

## Running Tests

```bash
# Backend (99 tests)
cd document-parser
pytest tests/ -v

# Frontend (81 tests)
cd frontend
npm run test:run
```

All tests must pass before submitting a PR.

## Submitting Changes

1. **Commit** with clear, descriptive messages
2. **Push** your branch to your fork
3. Open a **Pull Request** against `main`
4. Describe **what** changed and **why** in the PR description
5. Ensure CI passes (tests + build)

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Add tests for new functionality
- Update documentation if behavior changes
- Follow existing code style and conventions

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include steps to reproduce for bugs
- Mention your OS, Python/Node version, and Docker version if relevant

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
