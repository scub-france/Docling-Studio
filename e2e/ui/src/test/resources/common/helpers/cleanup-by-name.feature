@ignore
Feature: Helper — Delete a document by filename

  # Callable feature: finds a document by name via API and deletes it
  # Usage: * call read('classpath:common/helpers/cleanup-by-name.feature') { filename: 'small.pdf' }

  Scenario:
    Given url baseUrl
    And path '/api/documents'
    When method GET
    Then status 200
    * def matches = karate.filter(response, function(d){ return d.filename == filename })
    * if (karate.sizeOf(matches) > 0) karate.call('classpath:common/helpers/cleanup.feature', { docId: matches[0].id })
