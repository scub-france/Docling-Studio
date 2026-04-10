@e2e @ingestion
Feature: Ingestion pipeline — PDF → chunks → embeddings → OpenSearch

  Background:
    * url baseUrl

  Scenario: Upload PDF, analyze with chunking, ingest into OpenSearch, verify

    # Step 1: Check ingestion is available
    Given path '/api/ingestion/status'
    When method GET
    Then status 200
    And match response.available == true

    # Step 2: Upload a PDF
    Given path '/api/documents/upload'
    And multipart file file = { read: 'classpath:common/data/generated/medium.pdf', filename: 'medium.pdf', contentType: 'application/pdf' }
    When method POST
    Then status 200
    * def docId = response.id

    # Step 3: Create analysis with chunking
    Given path '/api/analyses'
    And request { documentId: '#(docId)', pipelineOptions: { doOcr: true, tableMode: 'fast' }, chunkingOptions: { chunkerType: 'hybrid', maxTokens: 256 } }
    When method POST
    Then status 200
    * def jobId = response.id

    # Step 4: Poll until completed
    Given path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    And match response.status == 'COMPLETED'
    And match response.chunksJson == '#string'

    # Step 5: Trigger ingestion
    Given path '/api/ingestion', jobId
    When method POST
    Then status 200
    And match response.docId == docId
    And match response.chunksIndexed == '#number'
    And assert response.chunksIndexed > 0
    And match response.embeddingDimension == '#number'
    And assert response.embeddingDimension > 0

    # Step 6: Cleanup — delete ingested data
    Given path '/api/ingestion', docId
    When method DELETE
    Then status 204

    # Step 7: Cleanup — delete analysis and document
    Given path '/api/analyses', jobId
    When method DELETE
    Then status 204

    Given path '/api/documents', docId
    When method DELETE
    Then status 204
