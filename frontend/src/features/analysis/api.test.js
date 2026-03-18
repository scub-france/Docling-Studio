import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createAnalysis, fetchAnalyses, fetchAnalysis, deleteAnalysis } from './api.js'

vi.mock('../../shared/api/http.js', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from '../../shared/api/http.js'

describe('analysis API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('createAnalysis sends POST with documentId', async () => {
    const job = { id: '1', documentId: 'doc-1', status: 'PENDING' }
    apiFetch.mockResolvedValue(job)

    const result = await createAnalysis('doc-1')

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses', {
      method: 'POST',
      body: JSON.stringify({ documentId: 'doc-1' }),
    })
    expect(result).toEqual(job)
  })

  it('fetchAnalyses calls GET /api/analyses', async () => {
    const jobs = [{ id: '1', status: 'COMPLETED' }]
    apiFetch.mockResolvedValue(jobs)

    const result = await fetchAnalyses()

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses')
    expect(result).toEqual(jobs)
  })

  it('fetchAnalysis calls GET /api/analyses/:id', async () => {
    const job = { id: '42', status: 'RUNNING' }
    apiFetch.mockResolvedValue(job)

    const result = await fetchAnalysis('42')

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses/42')
    expect(result).toEqual(job)
  })

  it('deleteAnalysis calls DELETE /api/analyses/:id', async () => {
    apiFetch.mockResolvedValue(null)

    await deleteAnalysis('42')

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses/42', { method: 'DELETE' })
  })
})
