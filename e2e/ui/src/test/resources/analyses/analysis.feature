@critical @ui
Feature: UI — Launch an analysis and verify results

  Background:
    * url baseUrl

  Scenario: Upload, analyze, and verify result tabs appear
    # Setup via API — upload a document
    * def result = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = result.docId

    # Open Studio page
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=doc-item]')

    # Select the uploaded document
    * click('[data-e2e=doc-item]')
    * waitFor('[data-e2e=doc-item].selected')

    # Verify we are in Configure mode (first toggle button is active)
    * waitFor('[data-e2e=toggle-btn].active')

    # Click Run / Exécuter
    * waitFor('[data-e2e=run-btn]')
    * click('[data-e2e=run-btn]')

    # Wait for analysis to complete
    * call read('classpath:common/helpers/ui-wait-analysis.feature')

    # Verify result tabs appear
    * waitFor('[data-e2e=result-tabs]')
    * waitFor('[data-e2e=tabs-header]')
    * match karate.sizeOf(locateAll('[data-e2e=tab-btn]')) == 3

    # Click on Markdown tab and verify content
    * def tabs = locateAll('[data-e2e=tab-btn]')
    * tabs[1].click()
    * waitFor('[data-e2e=raw-markdown]')
    * match text('[data-e2e=raw-content]') != ''

    # Switch to Elements tab
    * tabs[0].click()
    * waitFor('[data-e2e=elements-list]')
    * assert karate.sizeOf(locateAll('[data-e2e=element-card]')) > 0

    # Verify page indicator
    * waitFor('[data-e2e=page-indicator]')

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }
