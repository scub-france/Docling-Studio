import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from './api'

export type IngestionStep = 'embedding' | 'indexing' | 'done'

export const useIngestionStore = defineStore('ingestion', () => {
  const available = ref(false)
  const opensearchConnected = ref(false)
  const ingesting = ref(false)
  const error = ref<string | null>(null)
  /** Map of docId → chunks indexed count (tracks which docs are ingested) */
  const ingestedDocs = ref<Record<string, number>>({})
  /** Current step of the ingestion pipeline (null when idle) */
  const currentStep = ref<IngestionStep | null>(null)
  /** Search results */
  const searchResults = ref<api.SearchResultItem[]>([])
  const searchQuery = ref('')
  const searching = ref(false)

  let _pollTimer: ReturnType<typeof setInterval> | null = null

  async function checkAvailability(): Promise<void> {
    try {
      const status = await api.fetchIngestionStatus()
      available.value = status.available
      opensearchConnected.value = status.opensearchConnected
    } catch {
      available.value = false
      opensearchConnected.value = false
    }
  }

  function startPolling(intervalMs = 30_000): void {
    stopPolling()
    _pollTimer = setInterval(checkAvailability, intervalMs)
  }

  function stopPolling(): void {
    if (_pollTimer) {
      clearInterval(_pollTimer)
      _pollTimer = null
    }
  }

  async function ingest(jobId: string): Promise<api.IngestionResult | null> {
    ingesting.value = true
    error.value = null
    currentStep.value = 'embedding'
    try {
      currentStep.value = 'indexing'
      const result = await api.ingestAnalysis(jobId)
      currentStep.value = 'done'
      ingestedDocs.value[result.docId] = result.chunksIndexed
      return result
    } catch (e) {
      error.value = (e as Error).message || 'Ingestion failed'
      console.error('Ingestion failed', e)
      currentStep.value = null
      return null
    } finally {
      ingesting.value = false
      // Reset step after a short delay so the user sees the "done" state
      setTimeout(() => {
        currentStep.value = null
      }, 2000)
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

  async function search(query: string, docId?: string): Promise<void> {
    if (!query.trim()) {
      searchResults.value = []
      searchQuery.value = ''
      return
    }
    searching.value = true
    searchQuery.value = query
    try {
      const resp = await api.searchChunks(query, { docId })
      searchResults.value = resp.results
    } catch (e) {
      console.error('Search failed', e)
      searchResults.value = []
    } finally {
      searching.value = false
    }
  }

  function clearSearch(): void {
    searchResults.value = []
    searchQuery.value = ''
  }

  return {
    available,
    opensearchConnected,
    ingesting,
    error,
    ingestedDocs,
    currentStep,
    searchResults,
    searchQuery,
    searching,
    checkAvailability,
    startPolling,
    stopPolling,
    ingest,
    deleteIngested,
    search,
    clearSearch,
  }
})
