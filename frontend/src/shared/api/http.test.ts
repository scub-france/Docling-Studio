import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiFetch } from './http'

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sets Content-Type to application/json by default', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 1 }),
    })

    await apiFetch('/api/test')

    expect(spy).toHaveBeenCalledWith('/api/test', expect.objectContaining({
      headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
    }))
  })

  it('skips Content-Type when skipContentType is true', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    await apiFetch('/api/upload', { skipContentType: true })

    const headers = spy.mock.calls[0][1].headers
    expect(headers['Content-Type']).toBeUndefined()
  })

  it('returns parsed JSON on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: '123', name: 'doc.pdf' }),
    })

    const result = await apiFetch('/api/docs')
    expect(result).toEqual({ id: '123', name: 'doc.pdf' })
  })

  it('returns null on 204 No Content', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 204,
    })

    const result = await apiFetch('/api/docs/1', { method: 'DELETE' })
    expect(result).toBeNull()
  })

  it('throws on non-ok response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 404,
    })

    await expect(apiFetch('/api/docs/missing')).rejects.toThrow('API error: 404')
  })

  it('forwards method and body options', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    const body = JSON.stringify({ documentId: '42' })
    await apiFetch('/api/analyses', { method: 'POST', body })

    expect(spy).toHaveBeenCalledWith('/api/analyses', expect.objectContaining({
      method: 'POST',
      body,
    }))
  })

  it('merges custom headers with Content-Type', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    await apiFetch('/api/test', { headers: { 'X-Custom': 'value' } })

    const headers = spy.mock.calls[0][1].headers
    expect(headers['Content-Type']).toBe('application/json')
    expect(headers['X-Custom']).toBe('value')
  })
})
