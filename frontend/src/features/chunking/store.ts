import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Chunk, ChunkingOptions } from '../../shared/types'
import * as api from './api'

export const useChunkingStore = defineStore('chunking', () => {
  const rechunking = ref(false)
  const saving = ref(false)
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

  async function updateChunkText(
    jobId: string,
    chunkIndex: number,
    text: string,
  ): Promise<Chunk[]> {
    saving.value = true
    error.value = null
    try {
      return await api.updateChunkText(jobId, chunkIndex, text)
    } catch (e) {
      error.value = (e as Error).message || 'Failed to update chunk'
      console.error('Failed to update chunk', e)
      throw e
    } finally {
      saving.value = false
    }
  }

  return { rechunking, saving, error, rechunk, updateChunkText }
})
