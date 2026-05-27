import { describe, expect, it } from 'vitest'

import sampleDoclingDocument from './__fixtures__/sample-docling-document.json'
import { mergeAdjacentDoclingTexts, parseDoclingDocument } from './editing'
import { projectDoclingPages, projectDoclingTree } from './projection'

describe('docling projection', () => {
  it('projects page overlays from the document graph', () => {
    const doc = parseDoclingDocument(sampleDoclingDocument)

    const pages = projectDoclingPages(doc)

    expect(pages).toHaveLength(1)
    expect(pages[0]?.page_number).toBe(1)
    expect(pages[0]?.width).toBe(612)
    expect(pages[0]?.height).toBe(792)
    expect(pages[0]?.elements.map((element) => element.self_ref)).toEqual([
      '#/texts/0',
      '#/texts/1',
      '#/texts/2',
      '#/texts/3',
      '#/texts/4',
    ])
  })

  it('keeps both original provenance boxes when projecting merged texts', () => {
    const doc = mergeAdjacentDoclingTexts(
      parseDoclingDocument(sampleDoclingDocument),
      '#/texts/2',
      '#/texts/3',
    )

    const pages = projectDoclingPages(doc)
    const mergedBoxes = pages[0]?.elements.filter((element) => element.self_ref === '#/texts/2') ?? []

    expect(mergedBoxes).toHaveLength(2)
    expect(mergedBoxes[0]?.content).toBe('First paragraph. Second paragraph.')
    expect(mergedBoxes[1]?.content).toBe('First paragraph. Second paragraph.')
    expect(mergedBoxes[0]?.bbox).toEqual([10, 80, 220, 102])
    expect(mergedBoxes[1]?.bbox).toEqual([10, 110, 250, 132])
  })

  it('projects the parse tree from the document graph', () => {
    const doc = parseDoclingDocument(sampleDoclingDocument)

    const tree = projectDoclingTree(doc)

    expect(tree.map((node) => ({ ref: node.ref, type: node.type, label: node.label }))).toEqual([
      { ref: '#/texts/0', type: 'page_header', label: 'Sample Header' },
      { ref: '#/texts/1', type: 'section_header', label: 'Introduction' },
    ])
    expect(tree[1]?.children.map((child) => child.ref)).toEqual(['#/groups/0', '#/texts/4'])
    expect(tree[1]?.children[0]?.children).toEqual([])
  })
})
