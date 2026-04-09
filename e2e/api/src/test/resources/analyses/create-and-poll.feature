@regression
Feature: Create analysis and poll until completion

  Background:
    * url baseUrl
    * def analysisSchema = read('classpath:common/data/schemas/analysis.json')

  Scenario: Create analysis returns PENDING then completes
    # Upload document
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    # Create analysis
    Given path '/api/analyses'
    And request { documentId: '#(uploaded.docId)' }
    When method POST
    Then status 200
    And match response contains analysisSchema
    And match response.status == 'PENDING'
    And match response.documentId == uploaded.docId
    * def jobId = response.id

    # Poll until terminal state
    Given path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200

    # Verify completed result
    And match response.status == 'COMPLETED'
    And match response.contentMarkdown == '#string'
    And match response.contentHtml == '#string'
    And match response.pagesJson == '#string'
    And match response.startedAt == '#string'
    And match response.completedAt == '#string'

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Create analysis for non-existent document returns 404
    Given path '/api/analyses'
    And request { documentId: 'non-existent-id' }
    When method POST
    Then status 404

  Scenario: Get analysis by ID
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }

    Given path '/api/analyses', analysis.jobId
    When method GET
    Then status 200
    And match response contains analysisSchema
    And match response.id == analysis.jobId

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Get non-existent analysis returns 404
    Given path '/api/analyses', 'non-existent-id'
    When method GET
    Then status 404

  Scenario: List analyses returns array
    Given path '/api/analyses'
    When method GET
    Then status 200
    And match response == '#[]'
