import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from './api'

export const useIngestionStore = defineStore('ingestion', () => {
  const available = ref(false)
  const ingesting = ref(false)
  const error = ref<string | null>(null)
  /** Map of docId → chunks indexed count (tracks which docs are ingested) */
  const ingestedDocs = ref<Record<string, number>>({})

  async function checkAvailability(): Promise<void> {
    try {
      const status = await api.fetchIngestionStatus()
      available.value = status.available
    } catch {
      available.value = false
    }
  }

  async function ingest(jobId: string): Promise<api.IngestionResult | null> {
    ingesting.value = true
    error.value = null
    try {
      const result = await api.ingestAnalysis(jobId)
      ingestedDocs.value[result.docId] = result.chunksIndexed
      return result
    } catch (e) {
      error.value = (e as Error).message || 'Ingestion failed'
      console.error('Ingestion failed', e)
      return null
    } finally {
      ingesting.value = false
    }
  }

  async function deleteIngested(docId: string): Promise<void> {
    try {
      await api.deleteIngested(docId)
      delete ingestedDocs.value[docId]
    } catch (e) {
      error.value = (e as Error).message || 'Failed to delete ingested data'
      console.error('Failed to delete ingested data', e)
    }
  }

  return {
    available,
    ingesting,
    error,
    ingestedDocs,
    checkAvailability,
    ingest,
    deleteIngested,
  }
})
