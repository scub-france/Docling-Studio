@ignore
Feature: Helper — Upload a PDF document

  # Callable feature: returns { docId, response }
  # Usage: * def result = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }

  Scenario:
    * def filePath = 'classpath:common/data/generated/' + file
    Given url baseUrl
    And path '/api/documents/upload'
    And multipart file file = { read: '#(filePath)', filename: '#(file)', contentType: 'application/pdf' }
    When method POST
    Then status 200
    * def docId = response.id
