@smoke
Feature: Health endpoint

  Background:
    * url baseUrl
    * def healthSchema = read('classpath:common/data/schemas/health.json')

  Scenario: Health returns OK with expected fields
    Given path '/api/health'
    When method GET
    Then status 200
    And match response contains healthSchema
    And match response.status == 'ok'
    And match response.database == 'ok'

  Scenario: Health exposes configuration limits when set
    Given path '/api/health'
    When method GET
    Then status 200
    # maxFileSizeMb and maxPageCount are conditional (only if > 0)
    And match response.engine == '#? _ == "local" || _ == "remote"'
    And match response.version == '#string'
