import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSearchStore } from './store'
import * as api from './api'

vi.mock('./api', () => ({
  searchChunks: vi.fn(),
}))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useSearchStore', () => {
  describe('search', () => {
    it('stores results on success', async () => {
      vi.mocked(api.searchChunks).mockResolvedValue({
        results: [
          {
            docId: 'doc-1',
            filename: 'test.pdf',
            content: 'hello world',
            chunkIndex: 0,
            pageNumber: 1,
            score: 0.9,
            headings: [],
          },
        ],
        total: 1,
        query: 'hello',
      })
      const store = useSearchStore()
      await store.search('hello')
      expect(store.results).toHaveLength(1)
      expect(store.query).toBe('hello')
      expect(store.searching).toBe(false)
    })

    it('clears results on empty query', async () => {
      const store = useSearchStore()
      store.results = [
        {
          docId: 'doc-1',
          filename: 'test.pdf',
          content: 'hello',
          chunkIndex: 0,
          pageNumber: 1,
          score: 0.9,
          headings: [],
        },
      ]
      await store.search('')
      expect(store.results).toHaveLength(0)
      expect(store.query).toBe('')
    })

    it('clears results on error', async () => {
      vi.mocked(api.searchChunks).mockRejectedValue(new Error('fail'))
      const store = useSearchStore()
      await store.search('hello')
      expect(store.results).toHaveLength(0)
      expect(store.searching).toBe(false)
    })
  })

  describe('clear', () => {
    it('resets state', () => {
      const store = useSearchStore()
      store.query = 'test'
      store.results = [
        {
          docId: 'doc-1',
          filename: 'test.pdf',
          content: 'hello',
          chunkIndex: 0,
          pageNumber: 1,
          score: 0.9,
          headings: [],
        },
      ]
      store.clear()
      expect(store.query).toBe('')
      expect(store.results).toHaveLength(0)
    })
  })
})
