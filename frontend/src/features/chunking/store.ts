import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Chunk, ChunkingOptions } from '../../shared/types'
import * as api from './api'

export const useChunkingStore = defineStore('chunking', () => {
  const rechunking = ref(false)
  const error = ref<string | null>(null)

  async function rechunk(jobId: string, chunkingOptions: ChunkingOptions): Promise<Chunk[]> {
    rechunking.value = true
    error.value = null
    try {
      return await api.rechunkAnalysis(jobId, chunkingOptions)
    } catch (e) {
      error.value = (e as Error).message || 'Failed to rechunk'
      console.error('Failed to rechunk', e)
      throw e
    } finally {
      rechunking.value = false
    }
  }

  return { rechunking, error, rechunk }
})
