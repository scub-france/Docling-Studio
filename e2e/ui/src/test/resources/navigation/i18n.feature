@ui
Feature: UI — Language switch FR/EN

  Scenario: Switch language to French and back to English
    # Open settings page
    * driver uiBaseUrl + '/settings'
    * waitFor('[data-e2e=settings-panel]')

    # Ensure we start in EN (idempotent)
    * click('[data-e2e=lang-en]')
    * waitFor('[data-e2e=sidebar]')
    * match text('[data-e2e=sidebar]') contains 'Home'

    # Switch to FR
    * click('[data-e2e=lang-fr]')
    * waitFor('[data-e2e=sidebar]')
    * match text('[data-e2e=sidebar]') contains 'Accueil'

    # Switch back to EN (leave clean state)
    * click('[data-e2e=lang-en]')
    * waitFor('[data-e2e=sidebar]')
    * match text('[data-e2e=sidebar]') contains 'Home'
