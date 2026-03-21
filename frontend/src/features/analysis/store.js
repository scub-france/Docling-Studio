import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from './api.js'

export const useAnalysisStore = defineStore('analysis', () => {
  const analyses = ref([])
  const currentAnalysis = ref(null)
  const running = ref(false)
  const error = ref(null)
  const pollingInterval = ref(null)

  const currentPages = computed(() => {
    if (!currentAnalysis.value?.pagesJson) return []
    try {
      return JSON.parse(currentAnalysis.value.pagesJson)
    } catch {
      return []
    }
  })

  function clearError() { error.value = null }

  async function load() {
    try {
      error.value = null
      analyses.value = await api.fetchAnalyses()
    } catch (e) {
      error.value = e.message || 'Failed to load analyses'
      console.error('Failed to load analyses', e)
    }
  }

  async function run(documentId, pipelineOptions = null) {
    running.value = true
    error.value = null
    try {
      const analysis = await api.createAnalysis(documentId, pipelineOptions)
      currentAnalysis.value = analysis
      analyses.value.unshift(analysis)
      startPolling(analysis.id)
      return analysis
    } catch (e) {
      running.value = false
      error.value = e.message || 'Failed to start analysis'
      console.error('Failed to start analysis', e)
      throw e
    }
  }

  function startPolling(id) {
    stopPolling()
    pollingInterval.value = setInterval(async () => {
      try {
        const updated = await api.fetchAnalysis(id)
        currentAnalysis.value = updated
        const idx = analyses.value.findIndex(a => a.id === id)
        if (idx !== -1) analyses.value[idx] = updated
        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          stopPolling()
          running.value = false
        }
      } catch (e) {
        error.value = e.message || 'Polling error'
        console.error('Polling error', e)
        stopPolling()
        running.value = false
      }
    }, 2000)
  }

  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  }

  async function select(id) {
    try {
      currentAnalysis.value = await api.fetchAnalysis(id)
    } catch (e) {
      error.value = e.message || 'Failed to load analysis'
      console.error('Failed to load analysis', e)
    }
  }

  async function remove(id) {
    try {
      await api.deleteAnalysis(id)
      analyses.value = analyses.value.filter(a => a.id !== id)
      if (currentAnalysis.value?.id === id) currentAnalysis.value = null
    } catch (e) {
      error.value = e.message || 'Failed to delete analysis'
      console.error('Failed to delete analysis', e)
    }
  }

  return { analyses, currentAnalysis, currentPages, running, error, clearError, load, run, select, remove, stopPolling }
})
