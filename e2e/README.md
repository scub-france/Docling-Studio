# E2E API Tests — Karate

End-to-end API tests for Docling Studio using [Karate](https://karatelabs.github.io/karate/).

## Prerequisites

- **JDK 17+** (e.g. `brew install openjdk@17`)
- **Maven 3.9+** (e.g. `brew install maven`)
- **Python 3.12+** (for test data generation)
- **Docker** (for running the full stack)

## Quick start

```bash
# 1. Generate test PDFs
python e2e/generate-test-data.py

# 2. Start the stack
docker compose up -d --wait

# 3. Run all tests
mvn test -f e2e/pom.xml

# 4. Tear down
docker compose down
```

## Run by tag

```bash
# Smoke only (~30s)
mvn test -f e2e/pom.xml -Dkarate.options="--tags @smoke"

# Regression (~2min)
mvn test -f e2e/pom.xml -Dkarate.options="--tags @regression"

# Full E2E workflows (~5min)
mvn test -f e2e/pom.xml -Dkarate.options="--tags @e2e"
```

## Custom base URL

```bash
mvn test -f e2e/pom.xml -DbaseUrl=http://your-host:8000
```

## Structure

```
e2e/
├── generate-test-data.py       # Generates test PDFs (no binaries in repo)
├── pom.xml                     # Maven + Karate dependency
├── src/test/java/
│   └── E2ERunner.java          # JUnit5 Karate runner
└── src/test/resources/
    ├── karate-config.js        # Base URL, timeouts, retry config
    ├── common/
    │   ├── helpers/            # Callable features (upload, analyze, cleanup)
    │   └── data/
    │       ├── schemas/        # JSON match schemas
    │       ├── test-cases/     # Data-driven JSON files
    │       └── generated/      # Generated PDFs (gitignored)
    ├── health/                 # @smoke
    ├── documents/              # @regression
    ├── analyses/               # @regression
    └── workflows/              # @e2e (cross-domain)
```

## Reports

After a run, Karate HTML reports are in `e2e/target/karate-reports/`.
