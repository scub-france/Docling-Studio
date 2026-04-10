import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChunkingStore } from './store'

vi.mock('./api', () => ({
  rechunkAnalysis: vi.fn(),
  updateChunkText: vi.fn(),
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
    expect(store.saving).toBe(false)
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

  it('updateChunkText calls API and returns chunks', async () => {
    const chunks = [
      { text: 'updated', headings: [], sourcePage: 1, tokenCount: 5, bboxes: [], modified: true },
    ]
    vi.mocked(api.updateChunkText).mockResolvedValue(chunks)

    const store = useChunkingStore()
    const result = await store.updateChunkText('j1', 0, 'updated')

    expect(api.updateChunkText).toHaveBeenCalledWith('j1', 0, 'updated')
    expect(result).toEqual(chunks)
    expect(store.saving).toBe(false)
  })

  it('updateChunkText sets saving during execution', async () => {
    let resolve: (v: any) => void
    vi.mocked(api.updateChunkText).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r
        }),
    )

    const store = useChunkingStore()
    const promise = store.updateChunkText('j1', 0, 'updated')

    expect(store.saving).toBe(true)
    resolve!([])
    await promise
    expect(store.saving).toBe(false)
  })

  it('updateChunkText handles errors', async () => {
    vi.mocked(api.updateChunkText).mockRejectedValue(new Error('save failed'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useChunkingStore()
    await expect(store.updateChunkText('j1', 0, 'text')).rejects.toThrow('save failed')
    expect(store.saving).toBe(false)
    expect(store.error).toBe('save failed')
  })
})
