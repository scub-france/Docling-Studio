@regression
Feature: Re-chunking a completed analysis

  Background:
    * url baseUrl

  Scenario: Rechunk with default options returns chunks
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'medium.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }
    * assert analysis.response.status == 'COMPLETED'
    * assert analysis.response.hasDocumentJson == true

    Given path '/api/analyses', analysis.jobId, 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 512 } }
    When method POST
    Then status 200
    And match response == '#[_ > 0]'
    And match each response contains { text: '#string', tokenCount: '#number' }

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Rechunk with different max tokens changes results
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'medium.pdf' }
    * def analysis = call read('classpath:common/helpers/analyze.feature') { docId: '#(uploaded.docId)' }

    # Rechunk with small tokens
    Given path '/api/analyses', analysis.jobId, 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 64 } }
    When method POST
    Then status 200
    * def smallChunks = response

    # Rechunk with large tokens
    Given path '/api/analyses', analysis.jobId, 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 2048 } }
    When method POST
    Then status 200
    * def largeChunks = response

    # Smaller max tokens should produce more or equal chunks
    * assert smallChunks.length >= largeChunks.length

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Rechunk non-existent analysis returns 400
    Given path '/api/analyses', 'non-existent-id', 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 512 } }
    When method POST
    Then status 400
