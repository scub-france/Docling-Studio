import { describe, it, expect, vi, beforeEach } from 'vitest'
import { rechunkAnalysis } from './api'

vi.mock('../../shared/api/http', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from '../../shared/api/http'

describe('chunking API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
