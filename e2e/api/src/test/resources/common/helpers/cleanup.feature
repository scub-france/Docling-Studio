@ignore
Feature: Helper — Delete a document and its analyses

  # Callable feature: cleans up test data
  # Usage: * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }

  Scenario:
    Given url baseUrl
    And path '/api/documents', docId
    When method DELETE
    # Accept both 204 (deleted) and 404 (already gone)
    Then assert responseStatus == 204 || responseStatus == 404
