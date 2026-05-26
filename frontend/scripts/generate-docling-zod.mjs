import { readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import $RefParser from '@apidevtools/json-schema-ref-parser'
import { jsonSchemaToZod } from 'json-schema-to-zod'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const frontendRoot = path.resolve(__dirname, '..')
const inputPath = path.join(
  frontendRoot,
  'src/features/document/docling/docling-document.schema.json',
)
const outputPath = path.join(
  frontendRoot,
  'src/features/document/docling/docling-document.generated.ts',
)

const rawSchema = JSON.parse(await readFile(inputPath, 'utf8'))
const resolvedSchema = await $RefParser.dereference(rawSchema)
const moduleCode = jsonSchemaToZod(resolvedSchema, {
  depth: 20,
  module: 'esm',
  name: 'doclingDocument',
  type: 'DoclingDocument',
  zodVersion: 4,
})

await writeFile(outputPath, `${moduleCode}\n`)
