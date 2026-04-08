@e2e
Feature: Full happy path — upload to cleanup

  Background:
    * url baseUrl

  Scenario: Complete workflow — upload, analyze, verify, rechunk, cleanup
    # Step 1: Upload a PDF
    Given path '/api/documents/upload'
    And multipart file file = { read: 'classpath:common/data/generated/medium.pdf', filename: 'medium.pdf', contentType: 'application/pdf' }
    When method POST
    Then status 200
    And match response.pageCount == 5
    * def docId = response.id

    # Step 2: Verify document appears in list
    Given path '/api/documents'
    When method GET
    Then status 200
    And match response[*].id contains docId

    # Step 3: Get preview
    Given path '/api/documents', docId, 'preview'
    And param page = 1
    When method GET
    Then status 200
    And match header content-type contains 'image/png'

    # Step 4: Create analysis
    Given path '/api/analyses'
    And request { documentId: '#(docId)', pipelineOptions: { doOcr: true, tableMode: 'fast' } }
    When method POST
    Then status 200
    And match response.status == 'PENDING'
    * def jobId = response.id

    # Step 5: Poll until completed
    Given path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
    And match response.status == 'COMPLETED'
    And match response.contentMarkdown == '#string'
    And match response.contentHtml == '#string'
    And match response.pagesJson == '#string'
    And match response.hasDocumentJson == true

    # Step 6: Re-chunk the completed analysis
    Given path '/api/analyses', jobId, 'rechunk'
    And request { chunkingOptions: { chunkerType: 'hybrid', maxTokens: 256, mergePeers: true } }
    When method POST
    Then status 200
    And match response == '#[_ > 0]'
    And match each response contains { text: '#string', tokenCount: '#number' }

    # Step 7: Verify analysis appears in list
    Given path '/api/analyses'
    When method GET
    Then status 200
    And match response[*].id contains jobId

    # Step 8: Delete analysis
    Given path '/api/analyses', jobId
    When method DELETE
    Then status 204

    # Step 9: Delete document
    Given path '/api/documents', docId
    When method DELETE
    Then status 204

    # Step 10: Verify both are gone
    Given path '/api/documents', docId
    When method GET
    Then status 404

    Given path '/api/analyses', jobId
    When method GET
    Then status 404
