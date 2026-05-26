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

## Edit helpers

`editing.ts` contains immutable helpers that operate on a validated
`DoclingDocument` and return a newly validated document:

- `editDoclingText()`
- `reparentDoclingItem()`
- `mergeAdjacentDoclingTexts()`

These helpers intentionally mirror the current experimental backend semantics:

- edits work on serialized Docling JSON, not on page overlays or chunks
- merges require adjacent sibling text nodes under the same parent
- reparenting currently supports moving an item under a group or the document body
- every helper validates the resulting document through Zod before returning it

## Usage

```ts
import {
  editDoclingText,
  mergeAdjacentDoclingTexts,
  parseDoclingDocument,
  type DoclingDocument,
} from '@/features/document/docling'

const doc: DoclingDocument = parseDoclingDocument(rawJson)
const edited = editDoclingText(doc, '#/texts/12', 'Updated text')
const merged = mergeAdjacentDoclingTexts(edited, '#/texts/12', '#/texts/13')
```

The generated file is intentionally checked in so the frontend can type-check
without needing Python during normal UI work. Only regenerate it when the
upstream Docling model changes.
