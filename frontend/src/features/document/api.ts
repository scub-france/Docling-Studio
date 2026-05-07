import type { DocChunk, Document, DocTreeNode } from '../../shared/types'
import { apiFetch } from '../../shared/api/http'

export function fetchDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>('/api/documents')
}

export function fetchDocument(id: string): Promise<Document> {
  return apiFetch<Document>(`/api/documents/${id}`)
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch<Document>('/api/documents/upload', {
    method: 'POST',
    body: formData,
    skipContentType: true,
  })
}

export function deleteDocument(id: string): Promise<unknown> {
  return apiFetch(`/api/documents/${id}`, { method: 'DELETE' })
}

export function getPreviewUrl(id: string, page = 1, dpi = 150): string {
  return `/api/documents/${id}/preview?page=${page}&dpi=${dpi}`
}

/** Rechunk the canonical chunkset. Backend runs synchronously and returns
 * the new chunks — there is no async job to poll. */
export function rechunkDocument(id: string): Promise<DocChunk[]> {
  return apiFetch<DocChunk[]>(`/api/documents/${id}/rechunk`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export function fetchDocumentTree(id: string): Promise<DocTreeNode[]> {
  return apiFetch<DocTreeNode[]>(`/api/documents/${id}/tree`)
}
