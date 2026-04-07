import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from './store'

vi.mock('./api', () => ({
  fetchDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
}))

import * as api from './api'

describe('useDocumentStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with empty state', () => {
    const store = useDocumentStore()
    expect(store.documents).toEqual([])
    expect(store.selectedId).toBeNull()
    expect(store.uploading).toBe(false)
  })

  it('load() fetches and sets documents', async () => {
    const docs = [
      { id: '1', filename: 'a.pdf' },
      { id: '2', filename: 'b.pdf' },
    ]
    api.fetchDocuments.mockResolvedValue(docs)

    const store = useDocumentStore()
    await store.load()

    expect(store.documents).toEqual(docs)
  })

  it('load() handles errors gracefully', async () => {
    api.fetchDocuments.mockRejectedValue(new Error('network'))
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useDocumentStore()
    await store.load()

    expect(store.documents).toEqual([])
    spy.mockRestore()
  })

  it('upload() adds document to front of list and selects it', async () => {
    const newDoc = { id: 'new', filename: 'new.pdf' }
    api.uploadDocument.mockResolvedValue(newDoc)

    const store = useDocumentStore()
    store.documents = [{ id: 'old', filename: 'old.pdf' }]

    const result = await store.upload(new File([], 'new.pdf'))

    expect(result).toEqual(newDoc)
    expect(store.documents[0]).toEqual(newDoc)
    expect(store.selectedId).toBe('new')
    expect(store.uploading).toBe(false)
  })

  it('upload() sets uploading to true during upload', async () => {
    let resolveUpload
    api.uploadDocument.mockImplementation(
      () =>
        new Promise((r) => {
          resolveUpload = r
        }),
    )

    const store = useDocumentStore()
    const promise = store.upload(new File([], 'test.pdf'))

    expect(store.uploading).toBe(true)
    resolveUpload({ id: '1', filename: 'test.pdf' })
    await promise
    expect(store.uploading).toBe(false)
  })

  it('upload() resets uploading on error', async () => {
    api.uploadDocument.mockRejectedValue(new Error('fail'))
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const store = useDocumentStore()

    await expect(store.upload(new File([], 'test.pdf'))).rejects.toThrow('fail')
    expect(store.uploading).toBe(false)
  })

  it('remove() deletes document and clears selection if needed', async () => {
    api.deleteDocument.mockResolvedValue(null)

    const store = useDocumentStore()
    store.documents = [{ id: '1' }, { id: '2' }]
    store.selectedId = '1'

    await store.remove('1')

    expect(store.documents).toEqual([{ id: '2' }])
    expect(store.selectedId).toBeNull()
  })

  it('remove() does not clear selection for other documents', async () => {
    api.deleteDocument.mockResolvedValue(null)

    const store = useDocumentStore()
    store.documents = [{ id: '1' }, { id: '2' }]
    store.selectedId = '2'

    await store.remove('1')

    expect(store.selectedId).toBe('2')
  })

  it('select() sets selectedId', () => {
    const store = useDocumentStore()
    store.select('42')
    expect(store.selectedId).toBe('42')
  })
})
