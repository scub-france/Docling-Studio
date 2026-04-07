import { describe, it, expect, vi, beforeEach } from 'vitest'
import { rechunkAnalysis, createAnalysis } from '../analysis/api'

vi.mock('../../shared/api/http', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from '../../shared/api/http'

describe('chunking API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('createAnalysis sends chunkingOptions when provided', async () => {
    const job = { id: '1', documentId: 'doc-1', status: 'PENDING' }
    apiFetch.mockResolvedValue(job)

    const chunkingOpts = { chunker_type: 'hybrid' as const, max_tokens: 256 }
    await createAnalysis('doc-1', null, chunkingOpts)

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses', {
      method: 'POST',
      body: JSON.stringify({ documentId: 'doc-1', chunkingOptions: chunkingOpts }),
    })
  })

  it('createAnalysis omits chunkingOptions when null', async () => {
    apiFetch.mockResolvedValue({ id: '1' })

    await createAnalysis('doc-1', null, null)

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses', {
      method: 'POST',
      body: JSON.stringify({ documentId: 'doc-1' }),
    })
  })

  it('rechunkAnalysis sends POST to rechunk endpoint', async () => {
    const chunks = [{ text: 'chunk1', headings: [], sourcePage: 1, tokenCount: 10 }]
    apiFetch.mockResolvedValue(chunks)

    const opts = { chunker_type: 'hybrid' as const, max_tokens: 512 }
    const result = await rechunkAnalysis('job-1', opts)

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses/job-1/rechunk', {
      method: 'POST',
      body: JSON.stringify({ chunkingOptions: opts }),
    })
    expect(result).toEqual(chunks)
  })
})
