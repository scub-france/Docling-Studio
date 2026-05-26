# Docling Frontend Model

This folder keeps the frontend's typed view of a serialized `DoclingDocument`.

## Source of truth

- Python model: `docling_core.types.doc.document.DoclingDocument`
- JSON Schema export: `document-parser/scripts/export_docling_document_schema.py`
- Generated frontend schema: `docling-document.schema.json`
- Generated Zod model: `docling-document.generated.ts`

Regenerate both frontend artifacts with:

```bash
cd frontend
npm run generate:docling-model
```

## Why this exists

The parsed document graph is now intended to be editable directly in the frontend.
Using the exported JSON Schema plus a generated Zod 4 model gives us:

- runtime validation when loading or mutating document JSON
- an inferred `DoclingDocument` TypeScript type
- a stable place to build pure edit helpers before any API or persistence flow

## Modules

- `docling-document.schema.json`: checked-in JSON Schema exported from Python
- `docling-document.generated.ts`: generated Zod 4 model and inferred type
- `editing.ts`: pure document transforms and structural validation helpers
- `session.ts`: frontend-only draft editing session with undo/redo history

## Edit helpers

`editing.ts` contains immutable helpers that operate on a validated
`DoclingDocument` and return a newly validated document:

- `editDoclingText()`
- `moveDoclingItem()`
- `reparentDoclingItem()`
- `mergeAdjacentDoclingTexts()`
- `splitDoclingText()`
- `insertDoclingText()`
- `createDoclingGroup()`
- `deleteDoclingItem()`

## Structural guarantees

`parseDoclingDocument()` does more than schema validation. It also enforces:

- unique `self_ref` values
- reciprocal parent/child references
- no duplicate children under one parent
- no unreachable items outside the body/furniture roots
- no parent/child cycles

Collection-changing edits renormalize `#/groups/N` and `#/texts/N` refs before
returning so later items keep stable, schema-shaped references.

## Draft sessions

`DoclingDraftSession` is the frontend-only business-logic layer for standalone
editing work. It holds:

- a validated base document
- the current draft document
- undo/redo stacks
- typed `apply()` support via `DoclingEditOperation`
- `reset()` and `checkpoint()` lifecycle helpers

These helpers intentionally mirror the current experimental backend semantics:

- edits work on serialized Docling JSON, not on page overlays or chunks
- merges require adjacent sibling text nodes under the same parent
- editable parents are currently limited to the document body and group items
- every helper validates the resulting document through Zod before returning it
- every helper also validates graph-level structure, not only field shape

## Usage

```ts
import {
  DoclingDraftSession,
  editDoclingText,
  mergeAdjacentDoclingTexts,
  moveDoclingItem,
  parseDoclingDocument,
  type DoclingDocument,
} from '@/features/document/docling'

const doc: DoclingDocument = parseDoclingDocument(rawJson)
const edited = editDoclingText(doc, '#/texts/12', 'Updated text')
const merged = mergeAdjacentDoclingTexts(edited, '#/texts/12', '#/texts/13')
const moved = moveDoclingItem(merged, '#/texts/13', '#/groups/0', 0)

const session = new DoclingDraftSession(doc)
session.apply({ type: 'edit-text', itemRef: '#/texts/12', text: 'Updated text' })
session.undo()
```

The generated file is intentionally checked in so the frontend can type-check
without needing Python during normal UI work. Only regenerate it when the
upstream Docling model changes.

At this stage, none of this is wired into visible UI. The module is strictly a
frontend business-logic layer so the eventual editor can reuse tested,
standalone document transforms.
