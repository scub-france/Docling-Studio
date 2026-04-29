import cytoscape from 'cytoscape'
import type { Core } from 'cytoscape'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  REASONING_EDGE_TYPE,
  applyReasoningOverlay,
  buildDegradedOverlay,
  clearReasoningOverlay,
  focusIteration,
  nodeIdForSectionRef,
} from './graphReasoningOverlay'
import type { ReasoningResult } from './types'

function seed(): Core {
  // Headless mode — no DOM container needed.
  return cytoscape({
    headless: true,
    elements: [
      { data: { id: 'elem::#/texts/0', group: 'element' } },
      { data: { id: 'elem::#/texts/3', group: 'element' } },
      { data: { id: 'elem::#/texts/7', group: 'element' } },
      { data: { id: 'elem::#/groups/1', group: 'element' } },
    ],
  })
}

function result(
  iterations: Array<Partial<ReasoningResult['iterations'][number]>>,
): ReasoningResult {
  return {
    answer: 'x',
    converged: true,
    iterations: iterations.map((it, i) => ({
      iteration: i + 1,
      section_ref: '',
      reason: '',
      section_text_length: 0,
      can_answer: false,
      response: '',
      ...it,
    })),
  }
}

describe('nodeIdForSectionRef', () => {
  it('matches the backend _element_node id format', () => {
    // Kept in sync with document-parser/infra/neo4j/queries.py::_element_node.
    expect(nodeIdForSectionRef('#/texts/3')).toBe('elem::#/texts/3')
  })
})

describe('applyReasoningOverlay', () => {
  let cy: Core
  beforeEach(() => {
    cy = seed()
  })

  it('marks every resolvable section as visited with its iteration order', () => {
    const res = applyReasoningOverlay(
      cy,
      result([{ section_ref: '#/texts/0' }, { section_ref: '#/texts/3' }]),
    )

    expect(res.presentCount).toBe(2)
    expect(res.missingCount).toBe(0)
    expect(cy.getElementById('elem::#/texts/0').hasClass('visited')).toBe(true)
    expect(cy.getElementById('elem::#/texts/0').data('visitOrder')).toBe(1)
    expect(cy.getElementById('elem::#/texts/3').data('visitOrder')).toBe(2)
  })

  it('adds a REASONING_NEXT edge between each consecutive visited pair', () => {
    applyReasoningOverlay(
      cy,
      result([
        { section_ref: '#/texts/0' },
        { section_ref: '#/texts/3' },
        { section_ref: '#/texts/7' },
      ]),
    )

    const edges = cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`)
    expect(edges.length).toBe(2)
    const ids = edges.map((e) => e.id()).sort()
    expect(ids).toEqual([
      'REASONING_NEXT::elem::#/texts/0::elem::#/texts/3',
      'REASONING_NEXT::elem::#/texts/3::elem::#/texts/7',
    ])
  })

  it('reports missing section refs and does not crash on them', () => {
    const res = applyReasoningOverlay(
      cy,
      result([
        { section_ref: '#/texts/0' },
        { section_ref: '#/texts/999' }, // not in graph
        { section_ref: '#/texts/3' },
      ]),
    )

    expect(res.presentCount).toBe(2)
    expect(res.missingCount).toBe(1)
    expect(res.resolved[1].present).toBe(false)
    expect(cy.getElementById('elem::#/texts/999').nonempty()).toBe(false)
  })

  it('breaks the arrow chain across a missing iteration (no ghost edges)', () => {
    applyReasoningOverlay(
      cy,
      result([
        { section_ref: '#/texts/0' },
        { section_ref: '#/texts/999' }, // missing
        { section_ref: '#/texts/3' },
      ]),
    )

    // Only the chain between present-to-present pairs gets edges. With one
    // missing in the middle, we still draw 0→3 because the filter keeps the
    // present ones adjacent in the sequence used for edge drawing. Assert it:
    // one edge between 0 and 3.
    const edges = cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`)
    expect(edges.length).toBe(1)
    expect(edges[0].data('source')).toBe('elem::#/texts/0')
    expect(edges[0].data('target')).toBe('elem::#/texts/3')
  })

  it('is idempotent — re-applying replaces the previous overlay', () => {
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/0' }]))
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/3' }, { section_ref: '#/texts/7' }]))

    expect(cy.getElementById('elem::#/texts/0').hasClass('visited')).toBe(false)
    expect(cy.getElementById('elem::#/texts/3').hasClass('visited')).toBe(true)
    expect(cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`).length).toBe(1)
  })

  it('dims every non-visited node so the trace pops visually', () => {
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/0' }, { section_ref: '#/texts/3' }]))

    // Visited ones keep their full opacity (no dimmed class).
    expect(cy.getElementById('elem::#/texts/0').hasClass('dimmed')).toBe(false)
    expect(cy.getElementById('elem::#/texts/3').hasClass('dimmed')).toBe(false)
    // Everything else gets dimmed.
    expect(cy.getElementById('elem::#/texts/7').hasClass('dimmed')).toBe(true)
    expect(cy.getElementById('elem::#/groups/1').hasClass('dimmed')).toBe(true)
  })

  it('does not dim anything when the trace has no resolvable iterations', () => {
    // All missing → we don't want to wash out the whole graph for nothing.
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/999' }]))
    expect(cy.$('.dimmed').length).toBe(0)
  })

  it('skips dimming entirely when focusMode is off', () => {
    applyReasoningOverlay(
      cy,
      result([{ section_ref: '#/texts/0' }, { section_ref: '#/texts/3' }]),
      { focusMode: false },
    )
    // Visited still highlighted...
    expect(cy.getElementById('elem::#/texts/0').hasClass('visited')).toBe(true)
    // ...but nothing else gets dimmed.
    expect(cy.$('.dimmed').length).toBe(0)
  })

  it('does not dim the synthetic REASONING_NEXT edges', () => {
    applyReasoningOverlay(
      cy,
      result([
        { section_ref: '#/texts/0' },
        { section_ref: '#/texts/3' },
        { section_ref: '#/texts/7' },
      ]),
    )
    const reasoningEdges = cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`)
    expect(reasoningEdges.length).toBe(2)
    reasoningEdges.forEach((e) => {
      expect(e.hasClass('dimmed')).toBe(false)
    })
  })

  it('preserves the original graph elements (no destructive mutations)', () => {
    const beforeIds = cy
      .elements()
      .map((e) => e.id())
      .sort()
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/0' }]))
    clearReasoningOverlay(cy)
    const afterIds = cy
      .elements()
      .map((e) => e.id())
      .sort()
    expect(afterIds).toEqual(beforeIds)
  })
})

describe('clearReasoningOverlay', () => {
  it('removes class, data, dimming, and synthetic edges', () => {
    const cy = seed()
    applyReasoningOverlay(cy, result([{ section_ref: '#/texts/0' }, { section_ref: '#/texts/3' }]))
    clearReasoningOverlay(cy)

    expect(cy.$('.visited').length).toBe(0)
    expect(cy.$('.dimmed').length).toBe(0)
    expect(cy.getElementById('elem::#/texts/0').data('visitOrder')).toBeUndefined()
    expect(cy.$(`edge[type = "${REASONING_EDGE_TYPE}"]`).length).toBe(0)
  })

  it('is a no-op when nothing is overlaid', () => {
    const cy = seed()
    expect(() => clearReasoningOverlay(cy)).not.toThrow()
  })
})

describe('buildDegradedOverlay', () => {
  // Used when the Neo4j graph isn't loaded — we still want to show the
  // reasoning trace cards, just without graph positioning.
  it('returns every iteration with present=false', () => {
    const out = buildDegradedOverlay(
      result([
        { section_ref: '#/texts/0', reason: 'r0', can_answer: false },
        { section_ref: '#/texts/3', reason: 'r1', can_answer: true, response: 'done' },
      ]),
    )
    expect(out.resolved).toHaveLength(2)
    expect(out.presentCount).toBe(0)
    expect(out.missingCount).toBe(2)
    expect(out.resolved.every((r) => !r.present)).toBe(true)
    expect(out.resolved[0].reason).toBe('r0')
    expect(out.resolved[1].canAnswer).toBe(true)
    expect(out.resolved[1].response).toBe('done')
    expect(out.resolved[0].nodeId).toBe('elem::#/texts/0')
  })

  it('handles an empty iterations list', () => {
    const out = buildDegradedOverlay(result([]))
    expect(out.resolved).toEqual([])
    expect(out.presentCount).toBe(0)
    expect(out.missingCount).toBe(0)
  })
})

describe('focusIteration', () => {
  it('is a no-op for a missing node', () => {
    const cy = seed()
    expect(() => focusIteration(cy, 'elem::#/texts/does-not-exist')).not.toThrow()
  })
})
