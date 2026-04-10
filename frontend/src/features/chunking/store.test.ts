import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChunkingStore } from './store'

vi.mock('./api', () => ({
  rechunkAnalysis: vi.fn(),
}))

import * as api from './api'

describe('useChunkingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with default state', () => {
    const store = useChunkingStore()
    expect(store.rechunking).toBe(false)
    expect(store.error).toBeNull()
  })

  it('rechunk calls API and returns chunks', async () => {
    const chunks = [{ text: 'c1', headings: [], sourcePage: 1, tokenCount: 5, bboxes: [] }]
    vi.mocked(api.rechunkAnalysis).mockResolvedValue(chunks)

    const store = useChunkingStore()
    const result = await store.rechunk('j1', { chunker_type: 'hybrid', max_tokens: 256 })

    expect(api.rechunkAnalysis).toHaveBeenCalledWith('j1', {
      chunker_type: 'hybrid',
      max_tokens: 256,
    })
    expect(result).toEqual(chunks)
    expect(store.rechunking).toBe(false)
  })

  it('rechunk sets rechunking during execution', async () => {
    let resolve: (v: any) => void
    vi.mocked(api.rechunkAnalysis).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r
        }),
    )

    const store = useChunkingStore()
    const promise = store.rechunk('j1', { chunker_type: 'hybrid' })

    expect(store.rechunking).toBe(true)
    resolve!([])
    await promise
    expect(store.rechunking).toBe(false)
  })

  it('rechunk handles errors', async () => {
    vi.mocked(api.rechunkAnalysis).mockRejectedValue(new Error('fail'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useChunkingStore()
    await expect(store.rechunk('j1', { chunker_type: 'hybrid' })).rejects.toThrow('fail')
    expect(store.rechunking).toBe(false)
    expect(store.error).toBe('fail')
  })
})
