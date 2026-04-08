@regression
Feature: Document size validation

  Background:
    * url baseUrl

  Scenario: File within size limit is accepted
    Given path '/api/documents/upload'
    And multipart file file = { read: 'classpath:common/data/generated/small.pdf', filename: 'small.pdf', contentType: 'application/pdf' }
    When method POST
    Then status 200
    And match response.id == '#string'
    # Cleanup
    * def docId = response.id
    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(docId)' }

  Scenario: Health endpoint exposes max file size
    Given path '/api/health'
    When method GET
    Then status 200
    # maxFileSizeMb is present when > 0
    And match response.maxFileSizeMb == '#? _ == null || _ > 0'
