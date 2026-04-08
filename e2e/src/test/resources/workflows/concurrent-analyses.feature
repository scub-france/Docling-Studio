@e2e
Feature: Concurrent analysis execution

  Background:
    * url baseUrl

  Scenario: Multiple analyses complete successfully in parallel
    # Upload 3 documents
    * def doc1 = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def doc2 = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def doc3 = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    # Create 3 analyses
    Given path '/api/analyses'
    And request { documentId: '#(doc1.docId)' }
    When method POST
    Then status 200
    * def job1 = response.id

    Given path '/api/analyses'
    And request { documentId: '#(doc2.docId)' }
    When method POST
    Then status 200
    * def job2 = response.id

    Given path '/api/analyses'
    And request { documentId: '#(doc3.docId)' }
    When method POST
    Then status 200
    * def job3 = response.id

    # Poll all three until terminal state
    Given path '/api/analyses', job1
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    * def status1 = response.status

    Given path '/api/analyses', job2
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    * def status2 = response.status

    Given path '/api/analyses', job3
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    * def status3 = response.status

    # All three should have completed
    * match status1 == 'COMPLETED'
    * match status2 == 'COMPLETED'
    * match status3 == 'COMPLETED'

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(doc1.docId)' }
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(doc2.docId)' }
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(doc3.docId)' }
