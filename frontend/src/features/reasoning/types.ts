/**
 * Types mirroring the `docling-agent` reasoning-trace output (upstream type
 * name: `RAGResult`).
 *
 * The JSON imported by the user is produced either by:
 *   - the R&D sidecar (`experiments/reasoning-trace/inspect_doc.py`), or
 *   - any external `docling-agent` run that was serialized to JSON.
 *
 * Since `docling-agent` uses plain pydantic (no alias generator), field names
 * are **snake_case** here. This is one of the rare spots in the frontend where
 * we don't normalize to camelCase — keeping the shape 1:1 with upstream means
 * a schema drift upstream gives us a clean type error rather than silent
 * re-mapping.
 *
 * Source of truth: docling-project/docling-agent @ docling_agent/agent/rag_models.py
 */

export interface ReasoningIteration {
  iteration: number
  section_ref: string
  reason: string
  section_text_length: number
  can_answer: boolean
  response: string
}

export interface ReasoningResult {
  answer: string
  iterations: ReasoningIteration[]
  converged: boolean
}

/**
 * Envelope written by the R&D sidecar. The viewer also accepts a bare
 * `ReasoningResult` (see `parseImportedTrace` in the store).
 */
export interface SidecarEnvelope {
  job_id?: string
  filename?: string
  query?: string
  model?: { ollama_name?: string | null; hf_model_name?: string | null }
  max_iterations?: number
  result: ReasoningResult
}

/**
 * One iteration after matching its `section_ref` against the currently-loaded
 * Cytoscape graph. `present=false` means the section ref has no corresponding
 * node (doc not through Maintain, or a different version of the doc).
 */
export interface ResolvedIteration {
  iteration: number
  sectionRef: string
  nodeId: string
  present: boolean
  reason: string
  canAnswer: boolean
  response: string
  sectionTextLength: number
}

export interface OverlayResult {
  resolved: ResolvedIteration[]
  presentCount: number
  missingCount: number
}
