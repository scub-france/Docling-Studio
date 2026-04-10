# E2E Test Conventions — Karate & Karate UI

Rules and patterns for writing reliable, maintainable e2e tests in this project.

## Architecture

```
e2e/
├── generate-test-data.py   # Shared — generates PDFs for both suites
├── api/                    # Karate API tests (HTTP-only, no browser)
│   ├── pom.xml
│   └── src/test/...
└── ui/                     # Karate UI tests (browser, Chrome headless)
    ├── pom.xml
    └── src/test/...
```

API and UI are **peer projects** — same level, each with its own `pom.xml`, runner, and `karate-config.js`. Never nest one inside the other.

## Golden rules

### 1. Never use `Thread.sleep()` — use `retry()` or `waitFor()`

```gherkin
# BAD — blocks the thread, ignores Karate retry mechanism
* def wait = function(){ java.lang.Thread.sleep(2000) }
* wait()

# GOOD — uses Karate's built-in retry with logging
* retry(30, 1000).waitFor('.chunk-card')
```

For "wait until one of several conditions":

```gherkin
# GOOD — retry().script() returns truthy when the expression matches
* retry(120, 1000).script("document.querySelector('.result-tabs') || document.querySelector('.error')")
```

### 2. Never use `delay()` — use `waitFor()` on the expected outcome

```gherkin
# BAD — arbitrary wait, flaky on slow CI
* driver.inputFile('input[type=file]', filePath)
* delay(2000)
* waitFor('.doc-item')

# GOOD — wait for the actual result
* driver.inputFile('input[type=file]', filePath)
* waitFor('.doc-item')
```

The **only acceptable `delay()`** is for CSS animations that have no observable DOM change (e.g., a 250ms sidebar transition). Even then, prefer `retry().script()` on the final state.

### 3. Use `karate.sizeOf()` for element counts — never raw `.length`

```gherkin
# BAD — .length may return #notpresent depending on Karate context
* def tabs = locateAll('.tab-btn')
* match tabs.length == 3

# BAD — bypasses Karate's auto-wait and retry mechanisms
* def count = script("document.querySelectorAll('.tab-btn').length")

# GOOD — idiomatic Karate
* match karate.sizeOf(locateAll('.tab-btn')) == 3

# GOOD — for assertions with >
* assert karate.sizeOf(locateAll('.element-card')) > 0
```

### 4. Use `data-e2e` attributes — never depend on CSS classes

```gherkin
# BAD — breaks when a dev renames a class for styling
* waitFor('.doc-item')
* click('.chunk-card')

# BAD — breaks when locale is FR
* click('{a}History')

# GOOD — decoupled from CSS and i18n
* waitFor('[data-e2e=doc-item]')
* click('[data-e2e=chunk-card]')
* click('[data-e2e=nav-history]')
```

CSS classes are for **styling**, `data-e2e` attributes are for **testing**. A frontend dev must be free to rename `.doc-item` to `.document-card` without breaking a single test. Add `data-e2e="xxx"` to every element the tests interact with.

Convention for `data-e2e` values:
- **kebab-case**, descriptive: `doc-item`, `upload-zone`, `run-btn`, `result-tabs`
- **Unique per role**, not per instance: use `doc-item` for all doc items (plural via `locateAll`), `tab-btn` for all tabs
- **Never** use CSS class names as `data-e2e` values — if they happen to match today, rename the `data-e2e` to avoid confusion

If you must match on text (e.g., i18n test), set the locale explicitly first:

```gherkin
* click('{button}EN')
* waitFor('.sidebar')
# Now it's safe to assert on English text
```

### 5. Setup via API, verify via UI, cleanup via API

```gherkin
# Setup — fast, deterministic
* def result = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
* def docId = result.docId

# Verify — the actual UI test
* driver uiBaseUrl + '/studio'
* waitFor('.doc-item')
* click('.doc-item')
...

# Cleanup — fast, doesn't depend on UI state
* call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }
```

Exception: when the test IS about the UI action (e.g., upload.feature tests the upload UI itself).

### 6. Extract repeated patterns into callable helpers

```gherkin
# BAD — 5 lines of cleanup duplicated in every scenario
Given path '/api/documents'
When method GET
Then status 200
* def uploaded = karate.filter(response, function(d){ return d.filename == 'small.pdf' })
* def cleanupId = uploaded[0].id
* call read('classpath:common/helpers/cleanup.feature') { docId: '#(cleanupId)' }

# GOOD — one-liner via helper
* call read('classpath:common/helpers/cleanup-by-name.feature') { filename: 'small.pdf' }
```

Helpers go in `common/helpers/` with the `@ignore` tag and a doc comment showing usage.

### 7. Use `optional()` for elements that may or may not appear

```gherkin
# GOOD — doesn't fail if the chevron is already open
* def chevronOpen = optional('.config-chevron.open')
* if (!chevronOpen.present) click('.config-toggle')
```

Never `waitFor()` an element that might not exist (e.g., a spinner that flashes too fast).

## Tag strategy

| Tag | Scope | Run when |
|-----|-------|----------|
| `@critical` | 5 core user journeys | CI — merge to `main` |
| `@ui` | All UI features | Local dev |
| `@smoke` | API health checks | Every PR |
| `@regression` | API full coverage | PR to `release/*` |
| `@e2e` | API cross-domain workflows | PR to `release/*` |
| `@ignore` | Callable helpers | Never run directly |

## Driver config (karate-config.js)

```javascript
karate.configure('driver', {
  type: 'chrome',
  headless: true,
  showDriverLog: false,
  addOptions: ['--no-sandbox', '--disable-gpu'],  // required for CI Linux
  screenshotOnFailure: true                        // auto-screenshot on failure
});
```

- `--no-sandbox` — mandatory in GitHub Actions / Docker containers
- `--disable-gpu` — avoids GPU-related headless issues
- `screenshotOnFailure` — auto-captures the browser state on failure for debugging

## File naming

| File | Naming convention |
|------|-------------------|
| Feature files | `kebab-case.feature` (e.g., `batch-progress.feature`) |
| Helpers | `kebab-case.feature` in `common/helpers/`, prefixed `ui-` for UI-specific |
| Runners | `PascalCase.java` (e.g., `UIRunner.java`, `E2ERunner.java`) |
| Config | `karate-config.js` (Karate convention) |

## Running tests

```bash
# Generate test PDFs (required once, or after clean)
python3 e2e/generate-test-data.py

# API tests
mvn test -f e2e/api/pom.xml -Dkarate.options="--tags @smoke"

# UI tests — critical (CI scope)
mvn test -f e2e/ui/pom.xml -Dkarate.options="--tags @critical"

# UI tests — all (local scope)
mvn test -f e2e/ui/pom.xml -Dkarate.options="--tags @ui"
```

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| `locateAll().length` returns `#notpresent` | Use `karate.sizeOf(locateAll(...))` |
| `match x > 0` fails with "no step-definition" | Use `assert x > 0` for numeric comparisons |
| `if (...) call read(...)` fails with JS eval error | Use `karate.call()` inside `if` expressions |
| `input()` on `input[type=file]` crashes | Use `driver.inputFile()` for file inputs |
| `waitFor('.spinner')` times out on fast ops | Use `optional()` or skip — wait for the result instead |
| Nav links break when locale changes | Use `data-e2e` attributes, not text matchers |
| Tests break when CSS class is renamed | Use `[data-e2e=xxx]` selectors, never `.class-name` |
| Tests fail on CI but pass locally | Add `--no-sandbox` to Chrome options |
