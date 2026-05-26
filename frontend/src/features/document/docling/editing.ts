import { doclingDocument, type DoclingDocument } from './docling-document.generated'

type DoclingRef = { $ref: string }

type DoclingNode = {
  self_ref: string
  parent?: DoclingRef | null
  children?: DoclingRef[]
}

type DoclingTextItem = DoclingDocument['texts'][number] &
  DoclingNode & {
    text: string
    orig?: string | null
    prov?: DoclingProvenance[] | null
  }

type DoclingGroupItem = DoclingDocument['groups'][number] & DoclingNode

type DoclingBoundingBox = {
  l: number
  t: number
  r: number
  b: number
  coord_origin?: string
}

type DoclingProvenance = {
  page_no: number
  bbox?: DoclingBoundingBox | null
  charspan?: number[] | null
}

const ITEM_COLLECTION_KEYS = [
  'groups',
  'texts',
  'pictures',
  'tables',
  'key_value_items',
  'form_items',
  'field_regions',
  'field_items',
] as const

type ItemCollectionKey = (typeof ITEM_COLLECTION_KEYS)[number]

export class DoclingEditError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DoclingEditError'
  }
}

export function parseDoclingDocument(value: unknown): DoclingDocument {
  return doclingDocument.parse(value)
}

export function cloneDoclingDocument(doc: DoclingDocument): DoclingDocument {
  return parseDoclingDocument(structuredClone(doc))
}

export function stringifyDoclingDocument(doc: DoclingDocument): string {
  return JSON.stringify(doc, null, 2)
}

export function getDoclingItem(doc: DoclingDocument, ref: string): DoclingNode | null {
  if (doc.body.self_ref === ref) return doc.body as DoclingNode
  if (doc.furniture.self_ref === ref) return doc.furniture as DoclingNode

  for (const key of ITEM_COLLECTION_KEYS) {
    const item = (doc[key] as DoclingNode[]).find((candidate) => candidate.self_ref === ref)
    if (item) return item
  }

  return null
}

export function editDoclingText(
  doc: DoclingDocument,
  itemRef: string,
  text: string,
): DoclingDocument {
  const next = cloneDoclingDocument(doc)
  const item = requireTextItem(next, itemRef)

  item.text = text
  item.orig = text
  for (const provenance of item.prov ?? []) {
    provenance.charspan = [0, text.length]
  }

  return parseDoclingDocument(next)
}

export function reparentDoclingItem(
  doc: DoclingDocument,
  childRef: string,
  targetParentRef: string,
): DoclingDocument {
  if (childRef === '#/body' || childRef === '#/furniture') {
    throw new DoclingEditError(`Cannot move root item ${childRef}`)
  }
  if (childRef === targetParentRef) {
    throw new DoclingEditError('An item cannot become its own parent')
  }

  const next = cloneDoclingDocument(doc)
  const child = requireNode(next, childRef)
  const targetChildren = requireTargetChildren(next, targetParentRef)

  if (isDescendantRef(next, childRef, targetParentRef)) {
    throw new DoclingEditError('Cannot reparent an item into its own descendant')
  }

  const oldParentRef = child.parent?.$ref ?? null
  const oldChildren = getParentChildren(next, oldParentRef)
  if (oldChildren) {
    removeChildRef(oldChildren, childRef)
  }

  removeChildRef(targetChildren, childRef)
  targetChildren.push({ $ref: childRef })
  child.parent = { $ref: targetParentRef }

  return parseDoclingDocument(next)
}

export function mergeAdjacentDoclingTexts(
  doc: DoclingDocument,
  leadingRef: string,
  trailingRef: string,
  spacer = ' ',
): DoclingDocument {
  assertAdjacentTextSiblings(doc, leadingRef, trailingRef)

  const next = cloneDoclingDocument(doc)
  const leading = requireTextItem(next, leadingRef)
  const trailing = requireTextItem(next, trailingRef)
  const parentRef = leading.parent?.$ref ?? null
  const siblings = getParentChildren(next, parentRef)
  if (!siblings) {
    throw new DoclingEditError('Cannot resolve sibling order for merge')
  }

  leading.text = `${leading.text}${spacer}${trailing.text}`
  leading.orig = `${leading.orig ?? leading.text}${spacer}${trailing.orig ?? trailing.text}`
  mergeProvenance(leading, trailing)

  removeChildRef(siblings, trailingRef)
  removeItemFromCollection(next, trailingRef)

  return parseDoclingDocument(next)
}

function requireNode(doc: DoclingDocument, ref: string): DoclingNode {
  const item = getDoclingItem(doc, ref)
  if (!item) {
    throw new DoclingEditError(`Item not found: ${ref}`)
  }
  return item
}

function requireTextItem(doc: DoclingDocument, ref: string): DoclingTextItem {
  const item = requireNode(doc, ref)
  if (!isTextItem(item)) {
    throw new DoclingEditError(`Item ${ref} is not a text item`)
  }
  return item
}

function requireTargetChildren(doc: DoclingDocument, ref: string): DoclingRef[] {
  if (ref === '#/body') {
    return doc.body.children
  }

  const item = requireNode(doc, ref)
  if (!isGroupItem(item)) {
    throw new DoclingEditError(`Target parent is not a group or body: ${ref}`)
  }
  item.children ??= []
  return item.children
}

function isTextItem(value: DoclingNode): value is DoclingTextItem {
  return typeof (value as { text?: unknown }).text === 'string'
}

function isGroupItem(value: DoclingNode): value is DoclingGroupItem {
  return value.self_ref.startsWith('#/groups/')
}

function getParentChildren(doc: DoclingDocument, parentRef: string | null): DoclingRef[] | null {
  if (!parentRef || parentRef === '#/body') {
    return doc.body.children
  }
  if (parentRef === '#/furniture') {
    return doc.furniture.children
  }

  const item = getDoclingItem(doc, parentRef)
  return item?.children ?? null
}

function removeItemFromCollection(doc: DoclingDocument, ref: string): void {
  const collectionKey = getCollectionKey(ref)
  if (!collectionKey) {
    throw new DoclingEditError(`Cannot delete non-collection item ${ref}`)
  }

  const collection = doc[collectionKey] as DoclingNode[]
  const index = collection.findIndex((item) => item.self_ref === ref)
  if (index === -1) {
    throw new DoclingEditError(`Item not found in collection: ${ref}`)
  }
  collection.splice(index, 1)
}

function getCollectionKey(ref: string): ItemCollectionKey | null {
  const match = /^#\/([^/]+)\//.exec(ref)
  if (!match) return null
  const key = match[1] as ItemCollectionKey
  return ITEM_COLLECTION_KEYS.includes(key) ? key : null
}

function removeChildRef(children: DoclingRef[], ref: string): void {
  const index = children.findIndex((candidate) => candidate.$ref === ref)
  if (index !== -1) {
    children.splice(index, 1)
  }
}

function assertAdjacentTextSiblings(
  doc: DoclingDocument,
  leadingRef: string,
  trailingRef: string,
): void {
  const leading = requireTextItem(doc, leadingRef)
  const trailing = requireTextItem(doc, trailingRef)
  const leadingParent = leading.parent?.$ref ?? null
  const trailingParent = trailing.parent?.$ref ?? null

  if (leadingParent !== trailingParent) {
    throw new DoclingEditError('Text items must share the same parent to merge')
  }

  const siblings = getParentChildren(doc, leadingParent)
  if (!siblings) {
    throw new DoclingEditError('Cannot resolve sibling order for merge')
  }

  const refs = siblings.map((item) => item.$ref)
  const leadingIndex = refs.indexOf(leadingRef)
  const trailingIndex = refs.indexOf(trailingRef)

  if (leadingIndex === -1 || trailingIndex === -1) {
    throw new DoclingEditError('Text items are not present in the parent children list')
  }
  if (trailingIndex !== leadingIndex + 1) {
    throw new DoclingEditError('Text items must be adjacent siblings to merge')
  }
}

function mergeProvenance(leading: DoclingTextItem, trailing: DoclingTextItem): void {
  const leadingProv = leading.prov ?? []
  if (leadingProv.length === 0) {
    return
  }

  for (const provenance of leadingProv) {
    provenance.charspan = [0, leading.text.length]
  }

  const trailingProv = trailing.prov ?? []
  if (trailingProv.length === 0) {
    return
  }

  const leadBox = leadingProv[0]?.bbox
  const trailBox = trailingProv[0]?.bbox
  if (leadBox && trailBox) {
    leadingProv[0].bbox = {
      l: Math.min(leadBox.l, trailBox.l),
      t: Math.min(leadBox.t, trailBox.t),
      r: Math.max(leadBox.r, trailBox.r),
      b: Math.max(leadBox.b, trailBox.b),
      coord_origin: leadBox.coord_origin,
    }
  }

  if (trailingProv.length > 1) {
    leadingProv.push(...structuredClone(trailingProv.slice(1)))
  }
}

function isDescendantRef(doc: DoclingDocument, ancestorRef: string, candidateRef: string): boolean {
  const ancestor = getDoclingItem(doc, ancestorRef)
  if (!ancestor?.children?.length) {
    return false
  }

  for (const child of ancestor.children) {
    if (child.$ref === candidateRef) {
      return true
    }
    if (isDescendantRef(doc, child.$ref, candidateRef)) {
      return true
    }
  }

  return false
}
