import { apiFetch } from '../../shared/api/http'
import type { GraphPayload } from '../analysis/graphApi'
import type { ReasoningResult } from './types'

/**
 * Fetch the reasoning-trace graph for a document — built on the backend from
 * the SQLite `document_json` blob, not Neo4j. This is intentionally decoupled
 * from Maintain's richer Neo4j graph: reasoning only needs the structural
 * view (sections, parent/child, reading order, pages) to overlay iterations
 * onto, and should work even if Neo4j isn't configured.
 *
 * 404 if no completed analysis with `document_json` exists for the doc.
 */
export function fetchReasoningGraph(docId: string): Promise<GraphPayload> {
  return apiFetch<GraphPayload>(`/api/documents/${encodeURIComponent(docId)}/reasoning-graph`)
}

/**
 * Kick off a `docling-agent` reasoning run against a document and wait for
 * the `ReasoningResult` (no streaming yet — the backend blocks on `_rag_loop`
 * and returns once the loop converges or hits `max_iterations`).
 *
 * Runs typically take 20–40s depending on the model + Ollama latency. The
 * caller should show a loading state.
 *
 * Errors:
 *  - 503 if `REASONING_ENABLED=false` server-side or docling-agent isn't installed
 *  - 404 if no completed analysis exists for the doc
 *  - 500 if the loop itself raises (Ollama unreachable, model missing, …)
 */
export function runReasoning(
  docId: string,
  query: string,
  modelId?: string,
): Promise<ReasoningResult> {
  return apiFetch<ReasoningResult>(`/api/documents/${encodeURIComponent(docId)}/reasoning`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      // Backend accepts snake_case; don't camelCase here.
      model_id: modelId || undefined,
    }),
  })
}
