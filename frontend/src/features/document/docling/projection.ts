import type { DocTreeNode, Page, PageElement } from '../../../shared/types'
import type { DoclingDocument, DoclingNode } from './editing'

const DEFAULT_PAGE_WIDTH = 612
const DEFAULT_PAGE_HEIGHT = 792
const TREE_ITEM_COLLECTION_KEYS = ['texts', 'tables', 'pictures', 'groups'] as const

type TreeCollectionKey = (typeof TREE_ITEM_COLLECTION_KEYS)[number]

type InlineMeta = {
  text: string
}

type DoclingItemLike = DoclingNode & {
  label?: string | null
  text?: string | null
  name?: string | null
  level?: number | null
  prov?: Array<{
    page_no?: number | null
    bbox?: {
      l?: number | null
      t?: number | null
      r?: number | null
      b?: number | null
      coord_origin?: string | null
    } | null
  }> | null
}

/** Build the frontend overlay projection from a Docling document. */
export function projectDoclingPages(doc: DoclingDocument): Page[] {
  const pages = new Map<number, Page>()
  const rawPages = (doc.pages ?? {}) as Record<string, { size?: { width?: number; height?: number } }>

  for (const [pageKey, page] of Object.entries(rawPages)) {
    const pageNumber = Number(pageKey)
    if (!Number.isFinite(pageNumber)) continue
    pages.set(pageNumber, {
      page_number: pageNumber,
      width: page?.size?.width ?? DEFAULT_PAGE_WIDTH,
      height: page?.size?.height ?? DEFAULT_PAGE_HEIGHT,
      elements: [],
    })
  }

  for (const item of iterProjectablePageItems(doc)) {
    for (const prov of item.prov ?? []) {
      const pageNumber = Number(prov?.page_no)
      if (!Number.isFinite(pageNumber)) {
        continue
      }

      const page = ensurePage(pages, pageNumber)
      page.elements.push({
        type: getProjectedElementType(item),
        bbox: toTopLeftList(prov?.bbox, page.height),
        content: getProjectedPageContent(item),
        level: Number(item.level ?? 0),
        self_ref: item.self_ref || '',
      })
    }
  }

  return Array.from(pages.values()).sort((left, right) => left.page_number - right.page_number)
}

/** Build the parse-tree projection from a Docling document. */
export function projectDoclingTree(doc: DoclingDocument): DocTreeNode[] {
  const docData = doc as unknown as Record<string, unknown>
  const [skipRefs, inlineMeta] = buildCollapseIndex(doc)
  const byRef = new Map<string, DoclingItemLike>()

  for (const item of iterTreeItems(doc)) {
    if (item.self_ref) {
      byRef.set(item.self_ref, item)
    }
  }

  const root: DocTreeNode[] = []
  const stack: Array<{ level: number; children: DocTreeNode[] }> = [{ level: -1, children: root }]
  const bodyChildren = ((docData.body as { children?: Array<{ $ref?: string; cref?: string }> })?.children ?? [])

  const walk = (children: Array<{ $ref?: string; cref?: string }> | undefined): void => {
    if (!children) return
    for (const child of children) {
      const ref = child.$ref || child.cref
      if (!ref || skipRefs.has(ref)) continue
      const item = byRef.get(ref)
      if (!item) continue

      const labelType = normalizeLabelType(item.label)
      if (labelType === 'title' || labelType === 'section_header') {
        const level = labelType === 'title' ? 0 : Math.max(Number(item.level ?? 1), 1)
        while (stack.length > 1 && stack.at(-1)!.level >= level) {
          stack.pop()
        }
        const node = makeTreeNode(item, inlineMeta)
        stack.at(-1)!.children.push(node)
        stack.push({ level, children: node.children })
      } else {
        stack.at(-1)!.children.push(buildItemSubtree(item, byRef, skipRefs, inlineMeta))
      }
    }
  }

  walk(bodyChildren)
  return root
}

function iterProjectablePageItems(doc: DoclingDocument): DoclingItemLike[] {
  const collections = [
    getCollection(doc, 'texts'),
    getCollection(doc, 'pictures'),
    getCollection(doc, 'tables'),
    getCollection(doc, 'key_value_items'),
    getCollection(doc, 'form_items'),
    getCollection(doc, 'field_regions'),
    getCollection(doc, 'field_items'),
  ]
  return collections.flat() as DoclingItemLike[]
}

function iterTreeItems(doc: DoclingDocument): DoclingItemLike[] {
  return TREE_ITEM_COLLECTION_KEYS.flatMap((key) => getCollection(doc, key)) as DoclingItemLike[]
}

function buildItemSubtree(
  item: DoclingItemLike,
  byRef: Map<string, DoclingItemLike>,
  skipRefs: Set<string>,
  inlineMeta: Map<string, InlineMeta>,
): DocTreeNode {
  const node = makeTreeNode(item, inlineMeta)
  const labelType = normalizeLabelType(item.label)
  if (!['list', 'group', 'form_area', 'key_value_area'].includes(labelType)) {
    return node
  }

  for (const child of item.children ?? []) {
    const childRef = child.$ref
    if (!childRef || skipRefs.has(childRef)) continue
    const childItem = byRef.get(childRef)
    if (!childItem) continue
    node.children.push(buildItemSubtree(childItem, byRef, skipRefs, inlineMeta))
  }
  return node
}

function makeTreeNode(item: DoclingItemLike, inlineMeta: Map<string, InlineMeta>): DocTreeNode {
  const ref = item.self_ref || ''
  const type = normalizeLabelType(item.label)
  return {
    ref,
    type,
    label: displayTreeLabel(item, inlineMeta),
    children: [],
  }
}

function displayTreeLabel(item: DoclingItemLike, inlineMeta: Map<string, InlineMeta>): string {
  const ref = item.self_ref || ''
  const labelType = normalizeLabelType(item.label)
  if (isInlineGroup(item)) {
    const meta = inlineMeta.get(ref)
    if (meta?.text) {
      return truncate(meta.text)
    }
  }

  const text = (item.text || '').trim()
  if (text) {
    return truncate(text)
  }
  if (labelType === 'table') return 'Table'
  if (labelType === 'picture') return 'Figure'
  if (labelType === 'list') return 'List'
  if (labelType === 'group') return (item.name || 'Group').trim()
  return labelType || 'node'
}

function buildCollapseIndex(doc: DoclingDocument): [Set<string>, Map<string, InlineMeta>] {
  const byRef = new Map<string, DoclingItemLike>()
  for (const item of iterTreeItems(doc)) {
    if (item.self_ref) {
      byRef.set(item.self_ref, item)
    }
  }

  const skipRefs = new Set<string>()
  const inlineMeta = new Map<string, InlineMeta>()

  for (const item of byRef.values()) {
    const ref = item.self_ref || ''
    if (!ref) continue
    if (isInlineGroup(item)) {
      const textParts = collectInlineDescendants(ref, byRef, skipRefs)
      inlineMeta.set(ref, { text: textParts.join(' ') })
    } else if (isPicture(item)) {
      collectDescendants(ref, byRef, skipRefs)
    }
  }

  return [skipRefs, inlineMeta]
}

function collectDescendants(
  rootRef: string,
  byRef: Map<string, DoclingItemLike>,
  skipRefs: Set<string>,
): void {
  const walk = (ref: string): void => {
    const item = byRef.get(ref)
    if (!item) return
    for (const child of item.children ?? []) {
      const childRef = child.$ref
      if (!childRef || skipRefs.has(childRef)) continue
      skipRefs.add(childRef)
      walk(childRef)
    }
  }

  walk(rootRef)
}

function collectInlineDescendants(
  groupRef: string,
  byRef: Map<string, DoclingItemLike>,
  skipRefs: Set<string>,
): string[] {
  const textParts: string[] = []
  const walk = (ref: string): void => {
    const item = byRef.get(ref)
    if (!item) return
    for (const child of item.children ?? []) {
      const childRef = child.$ref
      if (!childRef || skipRefs.has(childRef)) continue
      skipRefs.add(childRef)
      const childItem = byRef.get(childRef)
      if (!childItem) continue
      if (isInlineGroup(childItem)) {
        walk(childRef)
        continue
      }
      const text = childItem.text || ''
      if (text) {
        textParts.push(text)
      }
    }
  }

  walk(groupRef)
  return textParts
}

function getProjectedElementType(item: DoclingItemLike): string {
  const label = normalizeLabelType(item.label)
  if (label === 'title') return 'title'
  if (label === 'section_header') return 'section_header'
  if (label === 'list') return 'list'
  if (label === 'formula') return 'formula'
  if (label === 'code') return 'code'
  if (label === 'caption') return 'caption'
  if (label === 'floating') return 'floating'
  if (label === 'picture' || label === 'chart') return 'picture'
  if (label === 'table') return 'table'
  return 'text'
}

function getProjectedPageContent(item: DoclingItemLike): string {
  if (normalizeLabelType(item.label) === 'table') {
    return (item.text || '').trim()
  }
  return item.text || ''
}

function ensurePage(pages: Map<number, Page>, pageNumber: number): Page {
  const existing = pages.get(pageNumber)
  if (existing) return existing
  const page: Page = {
    page_number: pageNumber,
    width: DEFAULT_PAGE_WIDTH,
    height: DEFAULT_PAGE_HEIGHT,
    elements: [],
  }
  pages.set(pageNumber, page)
  return page
}

function toTopLeftList(
  bbox: { l?: number | null; t?: number | null; r?: number | null; b?: number | null; coord_origin?: string | null } | null | undefined,
  pageHeight: number,
): [number, number, number, number] {
  if (!bbox) return [0, 0, 0, 0]
  const left = Number(bbox.l ?? 0)
  const top = Number(bbox.t ?? 0)
  const right = Number(bbox.r ?? 0)
  const bottom = Number(bbox.b ?? 0)
  const origin = (bbox.coord_origin || 'TOPLEFT').toUpperCase()
  if (origin === 'BOTTOMLEFT') {
    return [left, pageHeight - bottom, right, pageHeight - top]
  }
  return [left, top, right, bottom]
}

function truncate(text: string, maxLen = 80): string {
  const normalized = text.trim()
  if (normalized.length <= maxLen) {
    return normalized
  }
  return normalized.slice(0, maxLen - 1).trimEnd() + '…'
}

function normalizeLabelType(label: string | null | undefined): string {
  return (label || '').toLowerCase() || 'text'
}

function isInlineGroup(item: DoclingItemLike): boolean {
  return normalizeLabelType(item.label) === 'inline'
}

function isPicture(item: DoclingItemLike): boolean {
  return ['picture', 'chart'].includes(normalizeLabelType(item.label))
}

function getCollection(doc: DoclingDocument, key: TreeCollectionKey | 'pictures' | 'key_value_items' | 'form_items' | 'field_regions' | 'field_items'): DoclingNode[] {
  return ((doc as unknown as Record<string, DoclingNode[] | undefined>)[key] ?? []) as DoclingNode[]
}
