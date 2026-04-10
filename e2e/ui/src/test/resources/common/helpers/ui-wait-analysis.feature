@ignore
Feature: Helper — Wait for analysis to complete via UI polling

  # Callable feature: waits for analysis to finish — checks for result tabs or error state
  # Usage: * call read('classpath:common/helpers/ui-wait-analysis.feature')
  # Prerequisite: analysis must have been triggered, driver on the studio page

  Scenario:
    # Poll up to 2 minutes — result-tabs (COMPLETED) or error placeholder (FAILED)
    * retry(120, 1000).script("document.querySelector('[data-e2e=result-tabs]') || document.querySelector('[data-e2e=result-error]')")
