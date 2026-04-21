import { describe, expect, it } from 'vitest'

import type { GraphNode } from './graphApi'
import { LEGEND_CHIPS, findChip, partitionByHiddenChips } from './legendFilters'

function node(overrides: Partial<GraphNode>): GraphNode {
  return {
    id: overrides.id ?? 'n1',
    group: overrides.group ?? 'element',
    ...overrides,
  }
}

describe('LEGEND_CHIPS matching', () => {
  it('section matches only SectionHeader elements', () => {
    const chip = findChip('section')!
    expect(chip.match(node({ group: 'element', label: 'SectionHeader' }))).toBe(true)
    expect(chip.match(node({ group: 'element', label: 'Paragraph' }))).toBe(false)
    // An element with no label should NOT match section.
    expect(chip.match(node({ group: 'element' }))).toBe(false)
  })

  it('paragraph matches Paragraph and TextElement (fallback)', () => {
    const chip = findChip('paragraph')!
    expect(chip.match(node({ group: 'element', label: 'Paragraph' }))).toBe(true)
    // TextElement is the generic fallback Docling-labels that don't have a
    // specific mapping end up with. It's visually rendered in the paragraph
    // color, so the chip covers both.
    expect(chip.match(node({ group: 'element', label: 'TextElement' }))).toBe(true)
    expect(chip.match(node({ group: 'element', label: 'Table' }))).toBe(false)
  })

  it('group-based chips use `group` not `label`', () => {
    expect(findChip('document')!.match(node({ group: 'document' }))).toBe(true)
    expect(findChip('page')!.match(node({ group: 'page', page_no: 1 }))).toBe(true)
    expect(findChip('chunk')!.match(node({ group: 'chunk' }))).toBe(true)
    // document chip must NOT match elements that happen to have label===undefined
    expect(findChip('document')!.match(node({ group: 'element' }))).toBe(false)
  })

  it('exposes a stable list of chips', () => {
    // The sidebar CSS targets `.legend-${key}` — renaming a key here would
    // silently break the styles. Pin the expected order + keys.
    expect(LEGEND_CHIPS.map((c) => c.key)).toEqual([
      'document',
      'section',
      'paragraph',
      'table',
      'figure',
      'page',
      'chunk',
    ])
  })
})

describe('partitionByHiddenChips', () => {
  const nodes: GraphNode[] = [
    node({ id: 'd', group: 'document' }),
    node({ id: 's1', group: 'element', label: 'SectionHeader' }),
    node({ id: 'p1', group: 'element', label: 'Paragraph' }),
    node({ id: 'f1', group: 'element', label: 'Figure' }),
    node({ id: 'pg1', group: 'page' }),
  ]

  it('returns everything in `show` when the hidden set is empty', () => {
    const { hide, show } = partitionByHiddenChips(nodes, new Set())
    expect(hide).toHaveLength(0)
    expect(show).toHaveLength(nodes.length)
  })

  it('hides the nodes matching the selected chips', () => {
    const { hide, show } = partitionByHiddenChips(nodes, new Set(['figure', 'document']))
    expect(hide.map((n) => n.id).sort()).toEqual(['d', 'f1'])
    expect(show.map((n) => n.id).sort()).toEqual(['p1', 'pg1', 's1'])
  })

  it('ignores unknown chip keys (no silent breakage)', () => {
    const { hide, show } = partitionByHiddenChips(nodes, new Set(['some-new-kind']))
    expect(hide).toHaveLength(0)
    expect(show).toHaveLength(nodes.length)
  })

  it('keeps un-classifiable nodes visible even if all chips are off', () => {
    // A hypothetical element with an unmapped label (e.g. :Formula is in the
    // writer but has no chip yet) must not be hidden when toggling unrelated
    // chips — only explicit chip matches cause hiding.
    const weird = node({ id: 'w', group: 'element', label: 'Formula' })
    const { hide, show } = partitionByHiddenChips(
      [weird, ...nodes],
      new Set(['section', 'paragraph']),
    )
    expect(hide.map((n) => n.id)).toEqual(['s1', 'p1'])
    expect(show.some((n) => n.id === 'w')).toBe(true)
  })
})
