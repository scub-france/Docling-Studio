@ui
Feature: UI — Sidebar navigation

  Scenario: Navigate through all sidebar links
    * driver uiBaseUrl

    # Sidebar should be visible
    * waitFor('[data-e2e=sidebar]')

    # Verify all navigation items exist (each has data-e2e starting with nav-)
    * assert karate.sizeOf(locateAll('[data-e2e^=nav-]')) >= 4

    # Navigate to Studio via data-e2e (i18n-safe)
    * click('[data-e2e=nav-studio]')
    * waitForUrl('/studio')

    # Navigate to Documents
    * click('[data-e2e=nav-documents]')
    * waitForUrl('/documents')

    # Navigate to History
    * click('[data-e2e=nav-history]')
    * waitForUrl('/history')

    # Navigate to Settings
    * click('[data-e2e=nav-settings]')
    * waitForUrl('/settings')

    # Navigate back to Home via logo
    * click('[data-e2e=topbar-logo]')
    * waitForUrl(uiBaseUrl + '/')

  Scenario: Toggle sidebar collapse and expand
    * driver uiBaseUrl
    * waitFor('[data-e2e=sidebar]')

    # Sidebar should start with .open class
    * match attribute('[data-e2e=sidebar]', 'class') contains 'open'

    # Click burger menu to collapse
    * click('[data-e2e=burger-btn]')
    * retry(5, 300).script("!document.querySelector('[data-e2e=sidebar]').classList.contains('open')")
    * match attribute('[data-e2e=sidebar]', 'class') !contains 'open'

    # Toggle back to expand
    * click('[data-e2e=burger-btn]')
    * retry(5, 300).script("document.querySelector('[data-e2e=sidebar]').classList.contains('open')")
    * match attribute('[data-e2e=sidebar]', 'class') contains 'open'
