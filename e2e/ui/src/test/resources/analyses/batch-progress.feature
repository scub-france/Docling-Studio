@critical @ui
Feature: UI — Batch analysis progress bar

  Background:
    * url baseUrl

  Scenario: Upload large PDF, analyze, and verify progress or completion
    # Setup via API — upload a multi-page PDF for batch processing
    * def result = call read('classpath:common/helpers/upload.feature') { file: 'medium.pdf' }
    * def docId = result.docId

    # Open Studio page
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=doc-item]')

    # Select the document
    * click('[data-e2e=doc-item]')
    * waitFor('[data-e2e=doc-item].selected')

    # Click Run / Exécuter
    * waitFor('[data-e2e=run-btn]')
    * click('[data-e2e=run-btn]')

    # Wait for analysis to complete (progress bar may or may not appear)
    * call read('classpath:common/helpers/ui-wait-analysis.feature')

    # Verify results loaded
    * waitFor('[data-e2e=result-tabs]')
    * match karate.sizeOf(locateAll('[data-e2e=tab-btn]')) == 3

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }
