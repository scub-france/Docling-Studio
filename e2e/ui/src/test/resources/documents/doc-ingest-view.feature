@ui @regression
Feature: UI — Ingest view lists stores and pushes from the workspace (#225)

  # The third tab in the workspace switcher (Parse | Chunk | Ingest)
  # surfaces the document's ingestion state per store. The table loads
  # via GET /api/stores; the legacy /index/* paths redirect to /ingest/*.

  Background:
    * url baseUrl

  Scenario: Ingest tab renders the stores table
    * def upload = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = upload.docId

    # Doc + at least one completed analysis so the workspace has data
    # to act on.
    Given url baseUrl
    And path '/api/analyses'
    And request { documentId: '#(docId)', chunkingOptions: { chunkerType: 'hybrid', maxTokens: 256, mergePeers: true, repeatTableHeader: true } }
    When method POST
    Then status 200
    * def analysisId = response.id

    Given url baseUrl
    And path '/api/analyses', analysisId
    And retry until response.status == 'COMPLETED' || response.status == 'FAILED'
    When method GET
    Then status 200

    # Open the workspace on the Ingest mode.
    * driver uiBaseUrl + '/docs/' + docId + '?mode=ingest'
    * waitFor('[data-e2e=view-switcher]')
    * waitFor('[data-e2e=ingest-tab]')
    # Either the table or the "no stores configured" empty state must
    # show up — both are valid depending on the test environment.
    * def hasTable = exists('[data-e2e=ingest-table]')
    * def hasEmpty = exists('[data-e2e=ingest-no-stores]')
    * assert hasTable || hasEmpty

    * call read('classpath:common/helpers/cleanup-by-name.feature') { filename: 'small.pdf' }

  Scenario: ?mode=compare deep link aliases to ?mode=ingest
    * def upload = call read('classpath:common/helpers/upload.feature') { file: 'small.pdf' }
    * def docId = upload.docId

    * driver uiBaseUrl + '/docs/' + docId + '?mode=compare'
    * waitFor('[data-e2e=ingest-tab]')

    * call read('classpath:common/helpers/cleanup-by-name.feature') { filename: 'small.pdf' }
