import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHistoryStore } from './store.js'

vi.mock('./api.js', () => ({
  fetchAnalyses: vi.fn(),
  deleteAnalysis: vi.fn(),
}))

import * as api from './api.js'

describe('useHistoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with empty analyses', () => {
    const store = useHistoryStore()
    expect(store.analyses).toEqual([])
  })

  it('load() fetches analyses', async () => {
    const data = [{ id: '1' }, { id: '2' }]
    api.fetchAnalyses.mockResolvedValue(data)

    const store = useHistoryStore()
    await store.load()

    expect(store.analyses).toEqual(data)
  })

  it('load() handles errors gracefully', async () => {
    api.fetchAnalyses.mockRejectedValue(new Error('fail'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useHistoryStore()
    await store.load()

    expect(store.analyses).toEqual([])
  })

  it('remove() deletes and removes from list', async () => {
    api.deleteAnalysis.mockResolvedValue(null)

    const store = useHistoryStore()
    store.analyses = [{ id: '1' }, { id: '2' }, { id: '3' }]

    await store.remove('2')

    expect(store.analyses).toEqual([{ id: '1' }, { id: '3' }])
  })

  it('remove() handles errors gracefully', async () => {
    api.deleteAnalysis.mockRejectedValue(new Error('fail'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useHistoryStore()
    store.analyses = [{ id: '1' }]

    await store.remove('1')

    // Should not remove on error
    expect(store.analyses).toEqual([{ id: '1' }])
  })
})
