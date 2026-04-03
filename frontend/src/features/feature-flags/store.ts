import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '../../shared/api/http'

type ConversionEngine = 'local' | 'remote'

interface HealthResponse {
  status: string
  engine: ConversionEngine
}

export type FeatureFlag = 'chunking'

interface FeatureFlagDef {
  description: string
  isEnabled: (ctx: FeatureFlagContext) => boolean
}

interface FeatureFlagContext {
  engine: ConversionEngine | null
}

const featureRegistry: Record<FeatureFlag, FeatureFlagDef> = {
  chunking: {
    description: 'Document chunking for RAG preparation',
    isEnabled: (ctx) => ctx.engine === 'local',
  },
}

export const useFeatureFlagStore = defineStore('feature-flags', () => {
  const engine = ref<ConversionEngine | null>(null)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const context = computed<FeatureFlagContext>(() => ({
    engine: engine.value,
  }))

  function isEnabled(flag: FeatureFlag): boolean {
    if (!loaded.value) return false
    const def = featureRegistry[flag]
    return def.isEnabled(context.value)
  }

  async function load(): Promise<void> {
    try {
      const data = await apiFetch<HealthResponse>('/api/health')
      engine.value = data.engine
      loaded.value = true
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load feature flags'
      loaded.value = true
    }
  }

  return { engine, loaded, error, isEnabled, load }
})
