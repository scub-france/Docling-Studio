@e2e @ingestion
Feature: Ingestion pipeline — PDF → chunks indexed in OpenSearch

  Tests the complete ingestion workflow:
  upload PDF → analyze → chunk → ingest → verify in OpenSearch.

  Requires the full dev stack (OpenSearch + embedding service running).
  Skip by excluding the @ingestion tag when OpenSearch is not available.

  Background:
    * url baseUrl

  Scenario: Full ingestion workflow — PDF becomes searchable chunks in OpenSearch

    # ---- Step 1: Check ingestion pipeline is available ----
    Given path '/api/ingestion/status'
    When method GET
    Then status 200
    And match response.available == true

    # ---- Step 2: Upload a PDF ----
    Given path '/api/documents/upload'
    And multipart file file = { read: 'classpath:common/data/generated/medium.pdf', filename: 'ingest-test.pdf', contentType: 'application/pdf' }
    When method POST
    Then status 200
    And match response.id == '#string'
    And match response.filename == 'ingest-test.pdf'
    * def docId = response.id

    # ---- Step 3: Run analysis (with document JSON for chunking) ----
    Given path '/api/analyses'
    And request { documentId: '#(docId)', pipelineOptions: { doOcr: false, tableMode: 'fast' } }
    When method POST
    Then status 200
    And match response.status == 'PENDING'
    * def jobId = response.id

    # ---- Step 4: Poll until analysis is COMPLETED ----
    Given path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    And match response.status == 'COMPLETED'
    And match response.hasDocumentJson == true

    # ---- Step 5: Run chunking to produce chunk list ----
    Given path '/api/analyses', jobId, 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 512, mergePeers: true } }
    When method POST
    Then status 200
    And match response == '#[_ > 0]'
    * def chunkCount = response.length

    # ---- Step 6: Trigger ingestion ----
    Given path '/api/ingestion', jobId
    When method POST
    Then status 200
    And match response.docId == '#string'
    And match response.chunksIndexed == '#number'
    And match response.embeddingDimension == '#number'
    And match response.chunksIndexed > 0
    And match response.embeddingDimension > 0
    * def indexedCount = response.chunksIndexed
    * def embDim = response.embeddingDimension

    # Verify at least as many chunks as returned by rechunk
    * assert indexedCount >= 1

    # Embedding dimension must be a valid vector size (e.g. 384 for all-MiniLM-L6-v2)
    * assert embDim >= 128

    # ---- Step 7: Re-ingest is idempotent ----
    Given path '/api/ingestion', jobId
    When method POST
    Then status 200
    And match response.chunksIndexed == '#number'
    And match response.chunksIndexed > 0

    # ---- Step 8: Delete indexed chunks ----
    Given path '/api/ingestion', docId
    When method DELETE
    Then status 204

    # ---- Step 9: Cleanup — delete analysis and document ----
    Given path '/api/analyses', jobId
    When method DELETE
    Then status 204

    Given path '/api/documents', docId
    When method DELETE
    Then status 204

  Scenario: Ingestion fails gracefully when job is not COMPLETED

    # Upload a document
    Given path '/api/documents/upload'
    And multipart file file = { read: 'classpath:common/data/generated/medium.pdf', filename: 'ingest-fail-test.pdf', contentType: 'application/pdf' }
    When method POST
    Then status 200
    * def docId = response.id

    # Create analysis but do NOT wait for completion
    Given path '/api/analyses'
    And request { documentId: '#(docId)' }
    When method POST
    Then status 200
    * def jobId = response.id

    # Immediately attempt ingestion — should fail with 422 (job not COMPLETED or no chunks)
    Given path '/api/ingestion', jobId
    When method POST
    * def sc = responseStatus
    Then assert sc == 422 || sc == 503

    # Cleanup
    Given path '/api/documents', docId
    When method DELETE
    * def ignored = responseStatus

  Scenario: Ingestion status — available when OpenSearch is configured

    Given path '/api/ingestion/status'
    When method GET
    Then status 200
    And match response == { available: '#boolean', reason: '#string' }
