import { describe, it, expect, vi, beforeEach } from 'vitest'
import { searchChunks } from './api'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  mockFetch.mockReset()
})

describe('searchChunks', () => {
  it('calls /api/ingestion/search with query', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          results: [
            {
              docId: 'doc-1',
              filename: 'test.pdf',
              content: 'hello',
              chunkIndex: 0,
              pageNumber: 1,
              score: 0.95,
              headings: [],
            },
          ],
          total: 1,
          query: 'hello',
        }),
    })
    const result = await searchChunks('hello')
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/ingestion/search?q=hello',
      expect.objectContaining({ headers: { 'Content-Type': 'application/json' } }),
    )
    expect(result.results).toHaveLength(1)
    expect(result.results[0].score).toBe(0.95)
  })

  it('passes docId and k options', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ results: [], total: 0, query: 'test' }),
    })
    await searchChunks('test', { docId: 'doc-1', k: 5 })
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/ingestion/search?q=test&doc_id=doc-1&k=5',
      expect.objectContaining({ headers: { 'Content-Type': 'application/json' } }),
    )
  })
})
