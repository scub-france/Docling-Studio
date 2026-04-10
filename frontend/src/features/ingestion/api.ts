/**
 * Ingestion API client — wraps /api/ingestion endpoints.
 */

export interface IngestionResult {
  docId: string
  chunksIndexed: number
  embeddingDimension: number
}

export interface IngestionStatus {
  available: boolean
  reason: string
}

export async function ingestAnalysis(jobId: string): Promise<IngestionResult> {
  const resp = await fetch(`/api/ingestion/${jobId}`, { method: 'POST' })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.detail ?? `Ingestion failed (${resp.status})`)
  }
  return resp.json()
}

export async function deleteIngested(docId: string): Promise<void> {
  const resp = await fetch(`/api/ingestion/${docId}`, { method: 'DELETE' })
  if (!resp.ok && resp.status !== 404) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.detail ?? `Delete failed (${resp.status})`)
  }
}

export async function fetchIngestionStatus(): Promise<IngestionStatus> {
  const resp = await fetch('/api/ingestion/status')
  if (!resp.ok) {
    return { available: false, reason: `HTTP ${resp.status}` }
  }
  return resp.json()
}
