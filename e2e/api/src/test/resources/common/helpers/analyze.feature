@ignore
Feature: Helper — Create analysis and poll until terminal state

  # Callable feature: returns { jobId, response }
  # Usage: * def result = call read('classpath:common/helpers/analyze.feature') { docId: '#(docId)' }
  # Optional: { docId: '...', pipelineOptions: { tableMode: 'fast' } }

  Scenario:
    * def opts = karate.get('pipelineOptions', null)
    * def body = { documentId: '#(docId)' }
    * if (opts != null) body.pipelineOptions = opts

    # Create analysis
    Given url baseUrl
    And path '/api/analyses'
    And request body
    When method POST
    Then status 200
    * def jobId = response.id

    # Poll until COMPLETED or FAILED
    Given url baseUrl
    And path '/api/analyses', jobId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200
