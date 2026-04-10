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
    expect(result.docId).toBe('doc-1')
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ detail: 'job not completed' }),
    })
    await expect(ingestAnalysis('job-bad')).rejects.toThrow('job not completed')
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

  it('ignores 404 response', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404, json: () => Promise.resolve({}) })
    await expect(deleteIngested('doc-missing')).resolves.toBeUndefined()
  })

  it('throws on other errors', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'server error' }),
    })
    await expect(deleteIngested('doc-1')).rejects.toThrow('server error')
  })
})

describe('fetchIngestionStatus', () => {
  it('gets /api/ingestion/status', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ available: true, reason: '' }),
    })
    const result = await fetchIngestionStatus()
    expect(result.available).toBe(true)
  })

  it('returns unavailable on non-ok', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 503 })
    const result = await fetchIngestionStatus()
    expect(result.available).toBe(false)
  })
})
