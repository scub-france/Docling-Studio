@ui
Feature: UI — Pipeline configuration options

  Background:
    * url baseUrl

  Scenario: Toggle pipeline options in Configure mode
    # Setup via API
    * def result = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = result.docId

    # Open Studio
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=doc-item]')
    * click('[data-e2e=doc-item]')
    * waitFor('[data-e2e=doc-item].selected')

    # Verify config panel is visible in Configure mode
    * waitFor('[data-e2e=config-panel]')

    # Verify toggle switches exist (OCR, table structure, etc.)
    * assert karate.sizeOf(locateAll('[data-e2e=toggle-switch]')) > 0

    # Toggle OCR off then on
    * def firstToggle = locateAll('[data-e2e=toggle-label]')[0]
    * firstToggle.click()
    * firstToggle.click()

    # Verify select dropdown for table mode exists
    * assert karate.sizeOf(locateAll('[data-e2e=config-select]')) > 0

    # Change table mode
    * select('[data-e2e=config-select]', 'fast')

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }

  Scenario: Verify pipeline options are preserved across mode switches
    # Setup via API
    * def result = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = result.docId

    # Open Studio and select document
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=doc-item]')
    * click('[data-e2e=doc-item]')
    * waitFor('[data-e2e=doc-item].selected')

    # Change table mode to fast
    * waitFor('[data-e2e=config-select]')
    * select('[data-e2e=config-select]', 'fast')

    # Switch to Verify mode and back
    * click('[data-e2e~=verify-btn]')
    * waitFor('[data-e2e~=verify-btn].active')
    * click('[data-e2e~=configure-btn]')
    * waitFor('[data-e2e=config-select]')

    # Verify table mode is still fast
    * match value('[data-e2e=config-select]') == 'fast'

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }
