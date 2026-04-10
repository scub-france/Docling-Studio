import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHistoryStore } from './store'

vi.mock('./api', () => ({
  fetchHistory: vi.fn(),
  deleteHistoryEntry: vi.fn(),
}))

import * as api from './api'

describe('useHistoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with empty state', () => {
    const store = useHistoryStore()
    expect(store.analyses).toEqual([])
    expect(store.error).toBeNull()
  })

  it('load() fetches analyses', async () => {
    const analyses = [
      { id: 'a1', status: 'COMPLETED' },
      { id: 'a2', status: 'FAILED' },
    ]
    vi.mocked(api.fetchHistory).mockResolvedValue(analyses)

    const store = useHistoryStore()
    await store.load()

    expect(store.analyses).toEqual(analyses)
    expect(store.error).toBeNull()
  })

  it('load() handles errors gracefully', async () => {
    vi.mocked(api.fetchHistory).mockRejectedValue(new Error('network'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useHistoryStore()
    await store.load()

    expect(store.error).toBe('network')
  })

  it('remove() deletes and filters from list', async () => {
    vi.mocked(api.deleteHistoryEntry).mockResolvedValue(null)

    const store = useHistoryStore()
    store.analyses = [{ id: 'a1' }, { id: 'a2' }] as any[]
    await store.remove('a1')

    expect(store.analyses).toEqual([{ id: 'a2' }])
    expect(api.deleteHistoryEntry).toHaveBeenCalledWith('a1')
  })

  it('remove() handles errors gracefully', async () => {
    vi.mocked(api.deleteHistoryEntry).mockRejectedValue(new Error('fail'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useHistoryStore()
    store.analyses = [{ id: 'a1' }] as any[]
    await store.remove('a1')

    expect(store.error).toBe('fail')
    expect(store.analyses).toEqual([{ id: 'a1' }])
  })
})
