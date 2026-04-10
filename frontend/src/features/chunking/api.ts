import type { Chunk, ChunkingOptions } from '../../shared/types'
import { apiFetch } from '../../shared/api/http'

export function rechunkAnalysis(jobId: string, chunkingOptions: ChunkingOptions): Promise<Chunk[]> {
  return apiFetch<Chunk[]>(`/api/analyses/${jobId}/rechunk`, {
    method: 'POST',
    body: JSON.stringify({ chunkingOptions }),
  })
}
