import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIngestionStore } from './store'
import * as api from './api'

vi.mock('./api', () => ({
  fetchIngestionStatus: vi.fn(),
  ingestAnalysis: vi.fn(),
  deleteIngested: vi.fn(),
}))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useIngestionStore', () => {
  describe('checkAvailability', () => {
    it('sets available to true when API responds', async () => {
      vi.mocked(api.fetchIngestionStatus).mockResolvedValue({ available: true })
      const store = useIngestionStore()
      await store.checkAvailability()
      expect(store.available).toBe(true)
    })

    it('sets available to false on error', async () => {
      vi.mocked(api.fetchIngestionStatus).mockRejectedValue(new Error('fail'))
      const store = useIngestionStore()
      await store.checkAvailability()
      expect(store.available).toBe(false)
    })
  })

  describe('ingest', () => {
    it('calls API and tracks ingested doc', async () => {
      vi.mocked(api.ingestAnalysis).mockResolvedValue({
        docId: 'doc-1',
        chunksIndexed: 5,
        embeddingDimension: 384,
      })
      const store = useIngestionStore()
      const result = await store.ingest('job-1')
      expect(result?.chunksIndexed).toBe(5)
      expect(store.ingestedDocs['doc-1']).toBe(5)
      expect(store.ingesting).toBe(false)
    })

    it('sets error on failure', async () => {
      vi.mocked(api.ingestAnalysis).mockRejectedValue(new Error('fail'))
      const store = useIngestionStore()
      const result = await store.ingest('job-1')
      expect(result).toBeNull()
      expect(store.error).toBe('fail')
    })
  })

  describe('deleteIngested', () => {
    it('removes doc from tracked map', async () => {
      vi.mocked(api.deleteIngested).mockResolvedValue(null)
      const store = useIngestionStore()
      store.ingestedDocs['doc-1'] = 5
      await store.deleteIngested('doc-1')
      expect(store.ingestedDocs['doc-1']).toBeUndefined()
    })
  })
})
