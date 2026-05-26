import { describe, expect, it } from 'vitest'

import type { DoclingDocument } from './docling-document.generated'
import {
  DoclingEditError,
  editDoclingText,
  getDoclingItem,
  mergeAdjacentDoclingTexts,
  parseDoclingDocument,
  reparentDoclingItem,
} from './editing'

function makeDocument(): DoclingDocument {
  return parseDoclingDocument({
    name: 'Editable',
    body: {
      self_ref: '#/body',
      parent: null,
      children: [{ $ref: '#/texts/0' }, { $ref: '#/texts/1' }, { $ref: '#/groups/0' }],
      content_layer: 'body',
      name: '_root_',
      label: 'unspecified',
      meta: null,
    },
    groups: [
      {
        self_ref: '#/groups/0',
        parent: { $ref: '#/body' },
        children: [{ $ref: '#/texts/2' }],
        content_layer: 'body',
        name: 'group',
        label: 'section',
      },
    ],
    texts: [
      makeText('#/texts/0', '#/body', 'alpha', { l: 0, t: 0, r: 10, b: 10 }),
      makeText('#/texts/1', '#/body', 'beta', { l: 10, t: 0, r: 20, b: 10 }),
      makeText('#/texts/2', '#/groups/0', 'inside', { l: 20, t: 0, r: 30, b: 10 }),
    ],
  })
}

function makeText(
  selfRef: string,
  parentRef: string,
  text: string,
  bbox: { l: number; t: number; r: number; b: number },
) {
  return {
    self_ref: selfRef,
    parent: { $ref: parentRef },
    children: [],
    content_layer: 'body',
    label: 'paragraph',
    prov: [
      {
        page_no: 1,
        bbox: { ...bbox, coord_origin: 'TOPLEFT' },
        charspan: [0, text.length],
      },
    ],
    orig: text,
    text,
  }
}

describe('docling editing helpers', () => {
  it('edits text immutably and updates charspan', () => {
    const doc = makeDocument()

    const edited = editDoclingText(doc, '#/texts/0', 'alpha updated')

    expect(edited.texts[0].text).toBe('alpha updated')
    expect(edited.texts[0].orig).toBe('alpha updated')
    expect(edited.texts[0].prov?.[0]?.charspan).toEqual([0, 13])
    expect(doc.texts[0].text).toBe('alpha')
  })

  it('reparents an item into a group and updates child lists', () => {
    const doc = makeDocument()

    const moved = reparentDoclingItem(doc, '#/texts/1', '#/groups/0')
    const text = getDoclingItem(moved, '#/texts/1')

    expect(text?.parent?.$ref).toBe('#/groups/0')
    expect(moved.body.children.map((item) => item.$ref)).toEqual(['#/texts/0', '#/groups/0'])
    expect(moved.groups[0].children.map((item) => item.$ref)).toEqual(['#/texts/2', '#/texts/1'])
  })

  it('supports reparenting an item back to the body', () => {
    const doc = makeDocument()

    const moved = reparentDoclingItem(doc, '#/texts/2', '#/body')
    const text = getDoclingItem(moved, '#/texts/2')

    expect(text?.parent?.$ref).toBe('#/body')
    expect(moved.groups[0].children).toEqual([])
    expect(moved.body.children.at(-1)?.$ref).toBe('#/texts/2')
  })

  it('merges adjacent body text items and removes the trailing ref', () => {
    const doc = makeDocument()

    const merged = mergeAdjacentDoclingTexts(doc, '#/texts/0', '#/texts/1')

    expect(merged.texts).toHaveLength(2)
    expect(merged.texts[0].text).toBe('alpha beta')
    expect(merged.texts[0].orig).toBe('alpha beta')
    expect(merged.texts[0].prov?.[0]?.charspan).toEqual([0, 10])
    expect(merged.body.children.map((item) => item.$ref)).toEqual(['#/texts/0', '#/groups/0'])
  })

  it('rejects non-adjacent merges', () => {
    const doc = makeDocument()

    expect(() => mergeAdjacentDoclingTexts(doc, '#/texts/0', '#/texts/2')).toThrow(
      DoclingEditError,
    )
  })
})
