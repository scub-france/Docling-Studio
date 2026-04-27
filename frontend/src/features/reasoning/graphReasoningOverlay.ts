/**
 * Pure Cytoscape-manipulation helpers for the reasoning-trace overlay.
 *
 * Keeping this as a plain TS module (not a component) makes it trivially
 * testable against `cytoscape({ headless: true })` and lets the same code
 * drive both the v1 static-import UX and the v2 streaming-runner UX.
 *
 * The overlay is purely visual: it adds a class + a transient `visitOrder`
 * data attribute to existing element nodes and injects synthetic
 * `REASONING_NEXT` edges between successive visited nodes. None of this is
 * persisted to Neo4j.
 */
import type { Core } from 'cytoscape'

import type { OverlayResult, RAGResult, ResolvedIteration } from './types'

export const REASONING_EDGE_TYPE = 'REASONING_NEXT'
const VISITED_CLASS = 'visited'
const DIMMED_CLASS = 'dimmed'

/**
 * Build the Cytoscape node id for a given `section_ref`.
 *
 * Must stay in sync with `document-parser/infra/neo4j/queries.py::_element_node`
 * which emits `f"elem::{self_ref}"`. The `#` that lives inside a Docling
 * self_ref (e.g. `#/texts/3`) is fine inside an id string — we just always
 * look up via `cy.getElementById()` rather than the `#id` selector syntax,
 * which would conflict with the leading `#`.
 */
export function nodeIdForSectionRef(sectionRef: string): string {
  return `elem::${sectionRef}`
}

export interface OverlayOptions {
  /**
   * When true (default), dim every non-visited element and hide the Document
   * root — the user sees the trace pop against a muted background.
   * When false, the graph keeps its full colors; only visited nodes get the
   * orange ring + numbered badge and the REASONING_NEXT arrows are drawn.
   * Toggled from the ReasoningPanel header.
   */
  focusMode?: boolean
}

/**
 * Apply the overlay for a freshly imported `RAGResult`.
 *
 * Idempotent: any previous overlay is cleared first. Returns a summary that
 * the caller (store / panel) uses to drive the UI (list of iterations,
 * missing count, etc).
 */
export function applyReasoningOverlay(
  cy: Core,
  result: RAGResult,
  options: OverlayOptions = {},
): OverlayResult {
  const focusMode = options.focusMode ?? true
  clearReasoningOverlay(cy)

  const resolved: ResolvedIteration[] = result.iterations.map((it) => {
    const nodeId = nodeIdForSectionRef(it.section_ref)
    const node = cy.getElementById(nodeId)
    const present = node.nonempty()
    if (present) {
      node.addClass(VISITED_CLASS)
      node.data('visitOrder', it.iteration)
    }
    return {
      iteration: it.iteration,
      sectionRef: it.section_ref,
      nodeId,
      present,
      reason: it.reason,
      canAnswer: it.can_answer,
      response: it.response,
      sectionTextLength: it.section_text_length,
    }
  })

  // Dim everything that isn't part of the trace. We do this BEFORE injecting
  // the synthetic REASONING_NEXT edges so those edges never receive `.dimmed`
  // — they're the foreground of the viz. Takes the inspiration from the
  // BboxOverlay approach (dim non-highlighted bboxes, keep the active ones
  // fully opaque) and applies it to the graph.
  //
  // The Document root node is hidden outright (via a `display: none` rule on
  // `node.dimmed[group = "document"]`) — it sits at the center of the layout
  // and adds zero signal to a reasoning trace, only visual noise. Its
  // connected `HAS_ROOT` edge is hidden automatically by Cytoscape.
  const present = resolved.filter((r) => r.present)
  if (focusMode && present.length > 0) {
    cy.elements().not(`.${VISITED_CLASS}`).addClass(DIMMED_CLASS)
  }

  // Draw trace arrows only between successively-present iterations. Gaps
  // (missing nodes) break the chain — we don't draw edges to ghosts.
  for (let i = 0; i < present.length - 1; i++) {
    const src = present[i]
    const tgt = present[i + 1]
    cy.add({
      group: 'edges',
      data: {
        id: `${REASONING_EDGE_TYPE}::${src.nodeId}::${tgt.nodeId}`,
        source: src.nodeId,
        target: tgt.nodeId,
        type: REASONING_EDGE_TYPE,
        order: i,
      },
    })
  }

  const visitedEles = cy.$(`.${VISITED_CLASS}`)
  if (visitedEles.nonempty()) {
    // Padding keeps the arrows readable when the trace is one or two nodes.
    cy.fit(visitedEles, 80)
  }

  return {
    resolved,
    presentCount: present.length,
    missingCount: resolved.length - present.length,
  }
}

/**
 * Build a "degraded" overlay result when no Cytoscape instance is available
 * (graph failed to load, or graph is empty for this document). Every iteration
 * is marked `present: false`; the panel can still render the iteration cards
 * so the user sees the reasoning — they just don't get highlights on the graph.
 */
export function buildDegradedOverlay(result: RAGResult): OverlayResult {
  const resolved: ResolvedIteration[] = result.iterations.map((it) => ({
    iteration: it.iteration,
    sectionRef: it.section_ref,
    nodeId: nodeIdForSectionRef(it.section_ref),
    present: false,
    reason: it.reason,
    canAnswer: it.can_answer,
    response: it.response,
    sectionTextLength: it.section_text_length,
  }))
  return {
    resolved,
    presentCount: 0,
    missingCount: resolved.length,
  }
}

/**
 * Remove every overlay artifact from the graph. Safe to call when nothing
 * is overlaid — it becomes a no-op.
 */
export function clearReasoningOverlay(cy: Core): void {
  cy.$(`.${VISITED_CLASS}`).forEach((n) => {
    n.removeClass(VISITED_CLASS)
    n.removeData('visitOrder')
  })
  cy.$(`.${DIMMED_CLASS}`).removeClass(DIMMED_CLASS)
  cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`).remove()
}

/**
 * Center the viewport on a single iteration's node and give it a quick
 * visual pulse. No-op if the node isn't present (missing iteration).
 */
export function focusIteration(cy: Core, nodeId: string): void {
  const node = cy.getElementById(nodeId)
  if (!node.nonempty()) return
  cy.animate(
    {
      center: { eles: node },
      zoom: Math.max(cy.zoom(), 1.0),
    },
    { duration: 300 },
  )
  // flashClass is a cytoscape-builtin: add the class then remove it after N ms.
  node.flashClass('pulse', 800)
}

/**
 * Shape of a single Cytoscape stylesheet block used for the overlay. We keep
 * it intentionally loose (`Record<string, unknown>` for `style`) because the
 * upstream cytoscape types fork selectors by node-vs-edge prefix and flag
 * cross-type properties, while the runtime itself accepts everything we emit
 * here.
 */
interface StyleBlock {
  selector: string
  style: Record<string, unknown>
}

/**
 * Style rules appended to the existing GraphView stylesheet. Exported so the
 * component can spread them into its Cytoscape config.
 */
export const reasoningOverlayStyles: StyleBlock[] = [
  // Non-trace elements get dimmed — BboxOverlay-inspired: keep the colors,
  // drop the opacity hard so the trace pops. Node opacity cascades to label
  // + border; edges get a stronger fade because they add visual noise.
  {
    selector: `node.${DIMMED_CLASS}`,
    style: {
      opacity: 0.18,
      'text-opacity': 0.25,
    },
  },
  {
    selector: `edge.${DIMMED_CLASS}`,
    style: {
      opacity: 0.08,
    },
  },
  // Hide the Document root node entirely when a trace is active — it sits
  // at the center of the dagre layout and is pure noise for reasoning-path
  // inspection. Its `HAS_ROOT` edge is hidden automatically by Cytoscape
  // because `display: none` cascades to connected edges.
  {
    selector: `node.${DIMMED_CLASS}[group = "document"]`,
    style: {
      display: 'none',
    },
  },
  // Visited nodes: orange ring + label-less numbered badge above them.
  // Explicit opacity: 1 prevents inheritance quirks when the user re-applies
  // an overlay on top of an existing one.
  {
    selector: `node.${VISITED_CLASS}`,
    style: {
      'border-color': '#EA580C',
      'border-width': 4,
      'overlay-color': '#EA580C',
      'overlay-opacity': 0.08,
      'overlay-padding': 4,
      opacity: 1,
      'z-index': 50,
    },
  },
  {
    selector: `node.${VISITED_CLASS}[visitOrder]`,
    style: {
      label: 'data(visitOrder)',
      'text-valign': 'top',
      'text-margin-y': -6,
      'text-background-color': '#EA580C',
      'text-background-opacity': 1,
      'text-background-padding': '3px',
      'text-background-shape': 'roundrectangle',
      'text-border-color': '#FFFFFF',
      'text-border-width': 1.5,
      'text-border-opacity': 1,
      color: '#FFFFFF',
      'font-weight': 700,
      'font-size': 12,
      'text-opacity': 1,
    },
  },
  {
    selector: `edge[type = "${REASONING_EDGE_TYPE}"]`,
    style: {
      'line-color': '#EA580C',
      'target-arrow-color': '#EA580C',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.4,
      'curve-style': 'bezier',
      'control-point-step-size': 40,
      width: 3,
      opacity: 0.95,
      'z-index': 99,
    },
  },
  {
    selector: 'node.pulse',
    style: {
      'border-width': 7,
      'border-color': '#F59E0B',
    },
  },
]
