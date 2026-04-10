import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ingestAnalysis, deleteIngested, fetchIngestionStatus } from './api'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  mockFetch.mockReset()
})

describe('ingestAnalysis', () => {
  it('posts to /api/ingestion/:jobId', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ docId: 'doc-1', chunksIndexed: 5, embeddingDimension: 384 }),
    })
    const result = await ingestAnalysis('job-1')
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/ingestion/job-1',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.chunksIndexed).toBe(5)
  })
})

describe('deleteIngested', () => {
  it('deletes /api/ingestion/:docId', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 204, json: () => Promise.resolve(null) })
    await deleteIngested('doc-1')
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/ingestion/doc-1',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })
})

describe('fetchIngestionStatus', () => {
  it('gets /api/ingestion/status', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ available: true }),
    })
    const result = await fetchIngestionStatus()
    expect(result.available).toBe(true)
  })
})
