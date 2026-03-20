import { apiFetch } from '../../shared/api/http.js'

export function createAnalysis(documentId, pipelineOptions = null) {
  const body = { documentId }
  if (pipelineOptions) {
    body.pipelineOptions = pipelineOptions
  }
  return apiFetch('/api/analyses', {
    method: 'POST',
    body: JSON.stringify(body)
  })
}

export function fetchAnalyses() {
  return apiFetch('/api/analyses')
}

export function fetchAnalysis(id) {
  return apiFetch(`/api/analyses/${id}`)
}

export function deleteAnalysis(id) {
  return apiFetch(`/api/analyses/${id}`, { method: 'DELETE' })
}
