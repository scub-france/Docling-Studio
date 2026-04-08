@regression
Feature: Document CRUD operations

  Background:
    * url baseUrl
    * def docSchema = read('classpath:common/data/schemas/document.json')

  Scenario: List documents includes uploaded document
    # Upload
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    # List
    Given path '/api/documents'
    When method GET
    Then status 200
    And match response == '#[]'
    And match response[*].id contains uploaded.docId

    # Cleanup
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Get document by ID
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    Given path '/api/documents', uploaded.docId
    When method GET
    Then status 200
    And match response contains docSchema
    And match response.id == uploaded.docId
    And match response.filename == 'small.pdf'

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Get non-existent document returns 404
    Given path '/api/documents', 'non-existent-id'
    When method GET
    Then status 404

  Scenario: Delete document returns 204 then 404 on re-fetch
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    # Delete
    Given path '/api/documents', uploaded.docId
    When method DELETE
    Then status 204

    # Verify gone
    Given path '/api/documents', uploaded.docId
    When method GET
    Then status 404

  Scenario: Delete non-existent document returns 404
    Given path '/api/documents', 'non-existent-id'
    When method DELETE
    Then status 404
