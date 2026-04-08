@regression
Feature: Document page preview

  Background:
    * url baseUrl

  Scenario: Preview page 1 returns PNG
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    Given path '/api/documents', uploaded.docId, 'preview'
    And param page = 1
    When method GET
    Then status 200
    And match header content-type contains 'image/png'
    And match responseBytes == '#? _.length > 0'

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Preview with custom DPI
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    Given path '/api/documents', uploaded.docId, 'preview'
    And param page = 1
    And param dpi = 72
    When method GET
    Then status 200
    And match header content-type contains 'image/png'

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Preview page out of range returns 400
    * def uploaded = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

    Given path '/api/documents', uploaded.docId, 'preview'
    And param page = 999
    When method GET
    Then status 400
    And match response.detail contains 'out of range'

    * call read('classpath:common/helpers/cleanup.feature') { docId: '#(uploaded.docId)' }

  Scenario: Preview non-existent document returns 404
    Given path '/api/documents', 'non-existent-id', 'preview'
    When method GET
    Then status 404
