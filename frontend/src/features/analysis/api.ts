import type { Analysis, PipelineOptions } from '../../shared/types'
import { apiFetch } from '../../shared/api/http'

export function createAnalysis(
  documentId: string,
  pipelineOptions: PipelineOptions | null = null,
): Promise<Analysis> {
  const body: Record<string, unknown> = { documentId }
  if (pipelineOptions) {
    body.pipelineOptions = pipelineOptions
  }
  return apiFetch<Analysis>('/api/analyses', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function fetchAnalyses(): Promise<Analysis[]> {
  return apiFetch<Analysis[]>('/api/analyses')
}

export function fetchAnalysis(id: string): Promise<Analysis> {
  return apiFetch<Analysis>(`/api/analyses/${id}`)
}

export function deleteAnalysis(id: string): Promise<unknown> {
  return apiFetch(`/api/analyses/${id}`, { method: 'DELETE' })
}
