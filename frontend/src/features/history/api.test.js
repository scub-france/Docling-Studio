import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchAnalyses, deleteAnalysis } from './api.js'

vi.mock('../../shared/api/http.js', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from '../../shared/api/http.js'

describe('history API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchAnalyses calls GET /api/analyses', async () => {
    const data = [{ id: '1' }, { id: '2' }]
    apiFetch.mockResolvedValue(data)

    const result = await fetchAnalyses()

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses')
    expect(result).toEqual(data)
  })

  it('deleteAnalysis calls DELETE /api/analyses/:id', async () => {
    apiFetch.mockResolvedValue(null)

    await deleteAnalysis('5')

    expect(apiFetch).toHaveBeenCalledWith('/api/analyses/5', { method: 'DELETE' })
  })
})
