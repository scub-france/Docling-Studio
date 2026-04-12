@critical @ui
Feature: UI — Rechunk an analysis with different parameters

  Background:
    * url baseUrl

  Scenario: Analyze a document via UI then rechunk via Prepare tab
    # Setup via API — upload only (analysis will be done via UI)
    * def uploadResult = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = uploadResult.docId

    # Open Studio page
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=doc-item]')

    # Select the document
    * click('[data-e2e=doc-item]')
    * waitFor('[data-e2e=doc-item].selected')

    # Run analysis via UI (so the frontend store knows about it)
    * waitFor('[data-e2e=run-btn]')
    * click('[data-e2e=run-btn]')

    # Wait for analysis to complete
    * call read('classpath:common/helpers/ui-wait-analysis.feature')
    * waitFor('[data-e2e=result-tabs]')

    # Switch to Prepare tab — use dedicated selector (avoids race with feature flag load)
    * waitFor('[data-e2e~=prepare-btn]')
    * click('[data-e2e~=prepare-btn]')

    # Wait for chunk panel to load
    * waitFor('[data-e2e=chunk-panel]')

    # Expand config if collapsed
    * def chevronOpen = optional('[data-e2e=config-chevron].open')
    * if (!chevronOpen.present) click('[data-e2e=config-toggle]')
    * waitFor('[data-e2e=config-body]')

    # Modify max tokens — clear and set new value
    * clear('[data-e2e=config-input]')
    * input('[data-e2e=config-input]', '256')

    # Click the Chunk / Run button
    * waitFor('[data-e2e=chunk-btn]')
    * click('[data-e2e=chunk-btn]')

    # Wait for chunks to appear
    * retry(30, 1000).waitFor('[data-e2e=chunk-card]')

    # Verify chunk results
    * waitFor('[data-e2e=chunk-results]')
    * waitFor('[data-e2e=chunk-summary]')
    * assert karate.sizeOf(locateAll('[data-e2e=chunk-card]')) > 0

    # Verify each chunk has expected structure
    * waitFor('[data-e2e=chunk-index]')
    * waitFor('[data-e2e=chunk-tokens]')
    * waitFor('[data-e2e=chunk-text]')

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }
