@regression
Feature: Delete and cancel analysis jobs

  Background:
    * url baseUrl

  Scenario: Delete completed analysis
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }

    # Delete the analysis
    Given path '/api/analyses', analysis.jobId
    When method DELETE
    Then status 204

    # Verify it's gone
    Given path '/api/analyses', analysis.jobId
    When method GET
    Then status 404

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Delete non-existent analysis returns 404
    Given path '/api/analyses', 'non-existent-id'
    When method DELETE
    Then status 404

  Scenario: Delete document cascades to analyses
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }

    # Delete the document (should cascade)
    Given path '/api/documents', uploaded.docId
    When method DELETE
    Then status 204

    # Analysis should also be gone
    Given path '/api/analyses', analysis.jobId
    When method GET
    Then status 404
