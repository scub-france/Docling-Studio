import { describe, it, expect } from 'vitest'
import { useHistoryStore } from './store.js'
import { useAnalysisStore } from '../analysis/store.js'

describe('useHistoryStore', () => {
  it('is a re-export of useAnalysisStore', () => {
    expect(useHistoryStore).toBe(useAnalysisStore)
  })
})
