import { apiFetch } from '../../shared/api/http'
import type { GraphPayload } from '../analysis/graphApi'

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
