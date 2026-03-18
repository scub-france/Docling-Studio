import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchDocuments, fetchDocument, uploadDocument, deleteDocument, getPreviewUrl } from './api.js'

vi.mock('../../shared/api/http.js', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from '../../shared/api/http.js'

describe('document API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchDocuments calls GET /api/documents', async () => {
    const docs = [{ id: '1', filename: 'a.pdf' }]
    apiFetch.mockResolvedValue(docs)

    const result = await fetchDocuments()

    expect(apiFetch).toHaveBeenCalledWith('/api/documents')
    expect(result).toEqual(docs)
  })

  it('fetchDocument calls GET /api/documents/:id', async () => {
    const doc = { id: '42', filename: 'test.pdf' }
    apiFetch.mockResolvedValue(doc)

    const result = await fetchDocument('42')

    expect(apiFetch).toHaveBeenCalledWith('/api/documents/42')
    expect(result).toEqual(doc)
  })

  it('uploadDocument sends file via FormData with skipContentType', async () => {
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const response = { id: '1', filename: 'test.pdf' }
    apiFetch.mockResolvedValue(response)

    const result = await uploadDocument(file)

    expect(apiFetch).toHaveBeenCalledWith('/api/documents/upload', {
      method: 'POST',
      body: expect.any(FormData),
      skipContentType: true,
    })
    expect(result).toEqual(response)
  })

  it('deleteDocument calls DELETE /api/documents/:id', async () => {
    apiFetch.mockResolvedValue(null)

    await deleteDocument('42')

    expect(apiFetch).toHaveBeenCalledWith('/api/documents/42', { method: 'DELETE' })
  })

  it('getPreviewUrl builds correct URL with defaults', () => {
    expect(getPreviewUrl('abc')).toBe('/api/documents/abc/preview?page=1&dpi=150')
  })

  it('getPreviewUrl accepts custom page and dpi', () => {
    expect(getPreviewUrl('abc', 3, 300)).toBe('/api/documents/abc/preview?page=3&dpi=300')
  })
})
