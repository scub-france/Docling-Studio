import type { DoclingDocument } from './docling-document.generated'

import {
  createDoclingGroup,
  type DoclingCreateGroupOptions,
  deleteDoclingItem,
  DoclingEditError,
  editDoclingText,
  type DoclingIndex,
  insertDoclingText,
  mergeAdjacentDoclingTexts,
  moveDoclingItem,
  parseDoclingDocument,
  reparentDoclingItem,
  splitDoclingText,
  stringifyDoclingDocument,
  validateDoclingDocument,
  buildDoclingIndex,
  type DoclingInsertTextOptions,
} from './editing'

export type DoclingEditOperation =
  | { type: 'edit-text'; itemRef: string; text: string }
  | { type: 'move-item'; itemRef: string; targetParentRef: string; targetIndex?: number }
  | { type: 'reparent-item'; itemRef: string; targetParentRef: string }
  | { type: 'merge-texts'; leadingRef: string; trailingRef: string; spacer?: string }
  | { type: 'split-text'; itemRef: string; offset: number }
  | ({ type: 'insert-text' } & DoclingInsertTextOptions)
  | ({ type: 'create-group' } & DoclingCreateGroupOptions)
  | { type: 'delete-item'; itemRef: string }

/**
 * Frontend-only draft editor for standalone Docling manipulation.
 *
 * It keeps the current draft document plus undo/redo history, exposes a typed
 * operation API, and can checkpoint the current draft once a caller persists it.
 */
export class DoclingDraftSession {
  private baseDocumentValue: DoclingDocument
  private currentDocumentValue: DoclingDocument
  private undoStack: DoclingDocument[] = []
  private redoStack: DoclingDocument[] = []

  constructor(initial: DoclingDocument | unknown) {
    const parsed = parseDoclingDocument(initial)
    this.baseDocumentValue = parsed
    this.currentDocumentValue = parsed
  }

  get document(): DoclingDocument {
    return this.currentDocumentValue
  }

  get baseDocument(): DoclingDocument {
    return this.baseDocumentValue
  }

  get index(): DoclingIndex {
    return buildDoclingIndex(this.currentDocumentValue)
  }

  get canUndo(): boolean {
    return this.undoStack.length > 0
  }

  get canRedo(): boolean {
    return this.redoStack.length > 0
  }

  get hasChanges(): boolean {
    return stringifyDoclingDocument(this.currentDocumentValue) !== stringifyDoclingDocument(this.baseDocumentValue)
  }

  apply(operation: DoclingEditOperation): DoclingDocument {
    const next = applyDoclingEditOperation(this.currentDocumentValue, operation)
    this.undoStack.push(this.currentDocumentValue)
    this.currentDocumentValue = next
    this.redoStack = []
    return this.currentDocumentValue
  }

  undo(): DoclingDocument {
    if (!this.canUndo) {
      throw new DoclingEditError('Nothing to undo')
    }
    const previous = this.undoStack.pop() as DoclingDocument
    this.redoStack.push(this.currentDocumentValue)
    this.currentDocumentValue = previous
    return this.currentDocumentValue
  }

  redo(): DoclingDocument {
    if (!this.canRedo) {
      throw new DoclingEditError('Nothing to redo')
    }
    const next = this.redoStack.pop() as DoclingDocument
    this.undoStack.push(this.currentDocumentValue)
    this.currentDocumentValue = next
    return this.currentDocumentValue
  }

  reset(): DoclingDocument {
    this.currentDocumentValue = this.baseDocumentValue
    this.undoStack = []
    this.redoStack = []
    return this.currentDocumentValue
  }

  checkpoint(): DoclingDocument {
    this.baseDocumentValue = validateDoclingDocument(this.currentDocumentValue)
    this.undoStack = []
    this.redoStack = []
    return this.baseDocumentValue
  }

  replaceDocument(next: DoclingDocument | unknown): DoclingDocument {
    const parsed = parseDoclingDocument(next)
    this.baseDocumentValue = parsed
    this.currentDocumentValue = parsed
    this.undoStack = []
    this.redoStack = []
    return this.currentDocumentValue
  }
}

export function applyDoclingEditOperation(
  doc: DoclingDocument,
  operation: DoclingEditOperation,
): DoclingDocument {
  switch (operation.type) {
    case 'edit-text':
      return editDoclingText(doc, operation.itemRef, operation.text)
    case 'move-item':
      return moveDoclingItem(doc, operation.itemRef, operation.targetParentRef, operation.targetIndex)
    case 'reparent-item':
      return reparentDoclingItem(doc, operation.itemRef, operation.targetParentRef)
    case 'merge-texts':
      return mergeAdjacentDoclingTexts(doc, operation.leadingRef, operation.trailingRef, operation.spacer)
    case 'split-text':
      return splitDoclingText(doc, operation.itemRef, operation.offset)
    case 'insert-text':
      return insertDoclingText(doc, operation)
    case 'create-group':
      return createDoclingGroup(doc, operation)
    case 'delete-item':
      return deleteDoclingItem(doc, operation.itemRef)
    default: {
      const exhaustive: never = operation
      return exhaustive
    }
  }
}
