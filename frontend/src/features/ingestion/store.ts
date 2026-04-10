/**
 * Ingestion store — tracks which documents are indexed in OpenSearch
 * and exposes actions to ingest / delete indexed chunks.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deleteIngested, fetchIngestionStatus, ingestAnalysis } from './api'

export const useIngestionStore = defineStore('ingestion', () => {
  /** Map of docId → chunk count for indexed documents. */
  const ingestedDocs = ref<Record<string, number>>({})

  /** Whether the ingestion pipeline (OpenSearch + embedding) is available. */
  const available = ref(false)

  /** True while an ingestion is running. */
  const ingesting = ref(false)

  /** Last ingestion error message, if any. */
  const error = ref<string | null>(null)

  async function checkAvailability(): Promise<void> {
    try {
      const status = await fetchIngestionStatus()
      available.value = status.available
    } catch {
      available.value = false
    }
  }

  async function ingest(jobId: string, docId: string): Promise<number> {
    ingesting.value = true
    error.value = null
    try {
      const result = await ingestAnalysis(jobId)
      ingestedDocs.value = { ...ingestedDocs.value, [docId]: result.chunksIndexed }
      return result.chunksIndexed
    } catch (e) {
      error.value = (e as Error).message || 'Ingestion failed'
      throw e
    } finally {
      ingesting.value = false
    }
  }

  async function deleteIngestd(docId: string): Promise<void> {
    try {
      await deleteIngested(docId)
      const next = { ...ingestedDocs.value }
      delete next[docId]
      ingestedDocs.value = next
    } catch (e) {
      error.value = (e as Error).message || 'Delete failed'
      throw e
    }
  }

  function clearError(): void {
    error.value = null
  }

  return {
    ingestedDocs,
    available,
    ingesting,
    error,
    checkAvailability,
    ingest,
    deleteIngested: deleteIngestd,
    clearError,
  }
})
