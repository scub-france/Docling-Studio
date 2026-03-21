import { describe, it, expect } from 'vitest'
import { useHistoryStore } from './store'
import { useAnalysisStore } from '../analysis/store'

describe('useHistoryStore', () => {
  it('is a re-export of useAnalysisStore', () => {
    expect(useHistoryStore).toBe(useAnalysisStore)
  })
})
