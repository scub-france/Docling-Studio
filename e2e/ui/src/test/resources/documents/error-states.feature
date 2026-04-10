@ui
Feature: UI — Upload error states

  Scenario: Reject non-PDF file and show error message
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=upload-zone]')

    # Try to upload a non-PDF file
    * def filePath = karate.toAbsolutePath('classpath:common/data/generated/not-a-pdf.txt')
    * driver.inputFile('input[type=file]', filePath)

    # Verify error message is displayed
    * waitFor('[data-e2e=upload-error]')
    * match text('[data-e2e=upload-error]') contains 'PDF'

  Scenario: Upload hint displays max size info
    * driver uiBaseUrl + '/studio'
    * waitFor('[data-e2e=upload-zone]')

    # Verify upload hint is visible and not empty
    * waitFor('[data-e2e=upload-hint]')
    * match text('[data-e2e=upload-hint]') != ''
