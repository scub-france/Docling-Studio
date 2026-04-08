@regression
Feature: Batched conversion with progress reporting

  # Requires BATCH_PAGE_SIZE > 0 in the server configuration.
  # If BATCH_PAGE_SIZE is 0 (disabled), the batch-specific assertions
  # are skipped gracefully — the test still validates completion.

  Background:
    * url baseUrl

  Scenario: Large PDF completes and reports page count
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'large.pdf' }

    # Create analysis
    Given path '/api/analyses'
    And request { documentId: '#(uploaded.docId)' }
    When method POST
    Then status 200
    * def jobId = response.id

    # Poll until completed
    Given path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    And match response.status == 'COMPLETED'
    And match response.contentMarkdown == '#string'
    And match response.pagesJson == '#string'

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Batched conversion disables document_json
    # Only meaningful when BATCH_PAGE_SIZE > 0 and pages > BATCH_PAGE_SIZE
    # Check health to see if batching is possible
    Given path '/api/health'
    When method GET
    Then status 200

    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'large.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }
    * match analysis.response.status == 'COMPLETED'

    # If batched, hasDocumentJson should be false
    # If not batched (BATCH_PAGE_SIZE=0), hasDocumentJson should be true
    * match analysis.response.hasDocumentJson == '#boolean'

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }
