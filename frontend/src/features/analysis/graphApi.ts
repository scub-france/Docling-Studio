import { apiFetch } from '../../shared/api/http'

export interface GraphNode {
  id: string
  group: 'document' | 'element' | 'page' | 'chunk'
  label?: string
  docling_label?: string
  self_ref?: string
  text?: string
  prov_page?: number | null
  level?: number | null
  page_no?: number
  chunk_index?: number
  title?: string
  doc_id?: string
  token_count?: number
  [key: string]: unknown
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: 'HAS_ROOT' | 'PARENT_OF' | 'NEXT' | 'ON_PAGE' | 'HAS_CHUNK' | 'DERIVED_FROM'
  order?: number | null
}

export interface GraphPayload {
  doc_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  node_count: number
  edge_count: number
  truncated: boolean
  page_count: number
}

export function fetchDocumentGraph(docId: string): Promise<GraphPayload> {
  return apiFetch<GraphPayload>(`/api/documents/${encodeURIComponent(docId)}/graph`)
}
