import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from './api'

export const useSearchStore = defineStore('search', () => {
  const results = ref<api.SearchResultItem[]>([])
  const query = ref('')
  const searching = ref(false)

  async function search(q: string, docId?: string): Promise<void> {
    if (!q.trim()) {
      results.value = []
      query.value = ''
      return
    }
    searching.value = true
    query.value = q
    try {
      const resp = await api.searchChunks(q, { docId })
      results.value = resp.results
    } catch (e) {
      console.error('Search failed', e)
      results.value = []
    } finally {
      searching.value = false
    }
  }

  function clear(): void {
    results.value = []
    query.value = ''
  }

  return {
    results,
    query,
    searching,
    search,
    clear,
  }
})
