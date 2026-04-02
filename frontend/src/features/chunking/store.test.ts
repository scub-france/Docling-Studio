import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAnalysisStore } from '../analysis/store'

vi.mock('../analysis/api', () => ({
  createAnalysis: vi.fn(),
  fetchAnalyses: vi.fn().mockResolvedValue([]),
  fetchAnalysis: vi.fn(),
  deleteAnalysis: vi.fn(),
  rechunkAnalysis: vi.fn(),
}))

import * as api from '../analysis/api'

describe('analysis store — chunking', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('currentChunks parses chunksJson from current analysis', () => {
    const store = useAnalysisStore()
    const chunks = [
      { text: 'chunk1', headings: ['H1'], sourcePage: 1, tokenCount: 10 },
      { text: 'chunk2', headings: [], sourcePage: 2, tokenCount: 20 },
    ]
    store.currentAnalysis = {
      id: 'j1',
      documentId: 'd1',
      documentFilename: null,
      status: 'COMPLETED',
      contentMarkdown: null,
      contentHtml: null,
      pagesJson: null,
      chunksJson: JSON.stringify(chunks),
      hasDocumentJson: true,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: '2024-01-01',
    }
    expect(store.currentChunks).toEqual(chunks)
  })

  it('currentChunks returns empty array when no chunksJson', () => {
    const store = useAnalysisStore()
    store.currentAnalysis = {
      id: 'j1',
      documentId: 'd1',
      documentFilename: null,
      status: 'COMPLETED',
      contentMarkdown: null,
      contentHtml: null,
      pagesJson: null,
      chunksJson: null,
      hasDocumentJson: false,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: '2024-01-01',
    }
    expect(store.currentChunks).toEqual([])
  })

  it('rechunk calls API and refreshes analysis', async () => {
    const store = useAnalysisStore()
    const chunks = [{ text: 'c1', headings: [], sourcePage: 1, tokenCount: 5 }]
    vi.mocked(api.rechunkAnalysis).mockResolvedValue(chunks)
    vi.mocked(api.fetchAnalysis).mockResolvedValue({
      id: 'j1',
      documentId: 'd1',
      documentFilename: null,
      status: 'COMPLETED',
      contentMarkdown: null,
      contentHtml: null,
      pagesJson: null,
      chunksJson: JSON.stringify(chunks),
      hasDocumentJson: true,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: '2024-01-01',
    })

    store.currentAnalysis = {
      id: 'j1',
      documentId: 'd1',
      documentFilename: null,
      status: 'COMPLETED',
      contentMarkdown: null,
      contentHtml: null,
      pagesJson: null,
      chunksJson: null,
      hasDocumentJson: true,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: '2024-01-01',
    }

    const result = await store.rechunk('j1', { chunker_type: 'hybrid', max_tokens: 256 })

    expect(api.rechunkAnalysis).toHaveBeenCalledWith('j1', {
      chunker_type: 'hybrid',
      max_tokens: 256,
    })
    expect(result).toEqual(chunks)
    expect(store.rechunking).toBe(false)
  })

  it('run passes chunkingOptions to API', async () => {
    const store = useAnalysisStore()
    vi.mocked(api.createAnalysis).mockResolvedValue({
      id: 'j1',
      documentId: 'd1',
      documentFilename: null,
      status: 'PENDING',
      contentMarkdown: null,
      contentHtml: null,
      pagesJson: null,
      chunksJson: null,
      hasDocumentJson: false,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: '2024-01-01',
    })

    await store.run('d1', null, { chunker_type: 'hierarchical' })

    expect(api.createAnalysis).toHaveBeenCalledWith('d1', null, {
      chunker_type: 'hierarchical',
    })
  })
})
