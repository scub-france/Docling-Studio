import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '../../shared/api/http'
import { appMaxFileSizeMb, appMaxPageCount } from '../../shared/appConfig'

type ConversionEngine = 'local' | 'remote'
type DeploymentMode = 'self-hosted' | 'huggingface'

interface HealthResponse {
  status: string
  version?: string
  engine: ConversionEngine
  deploymentMode?: DeploymentMode
  maxPageCount?: number
  maxFileSizeMb?: number
  ingestionAvailable?: boolean
  reasoningAvailable?: boolean
}

export type FeatureFlag = 'chunking' | 'disclaimer' | 'ingestion' | 'reasoning'

interface FeatureFlagDef {
  description: string
  isEnabled: (ctx: FeatureFlagContext) => boolean
}

interface FeatureFlagContext {
  engine: ConversionEngine | null
  deploymentMode: DeploymentMode | null
  ingestionAvailable: boolean
  reasoningAvailable: boolean
}

const featureRegistry: Record<FeatureFlag, FeatureFlagDef> = {
  chunking: {
    description: 'Document chunking for RAG preparation',
    isEnabled: (ctx) => ctx.engine !== null,
  },
  disclaimer: {
    description: 'Show shared-instance disclaimer banner',
    isEnabled: (ctx) => ctx.deploymentMode === 'huggingface',
  },
  ingestion: {
    description: 'OpenSearch ingestion pipeline (embedding + vector indexing)',
    isEnabled: (ctx) => ctx.ingestionAvailable,
  },
  reasoning: {
    // Backend-gated: `reasoningAvailable` is true on `/api/health` only when
    // `REASONING_ENABLED=true` AND docling-agent + mellea are importable.
    // Hides the sidebar entry when the runner isn't wired, instead of
    // letting the user click through to a 503.
    description: 'Reasoning trace tunnel (docling-agent ReasoningResult viewer)',
    isEnabled: (ctx) => ctx.reasoningAvailable,
  },
}

export const useFeatureFlagStore = defineStore('feature-flags', () => {
  const engine = ref<ConversionEngine | null>(null)
  const deploymentMode = ref<DeploymentMode | null>(null)
  const maxPageCount = ref<number>(0)
  const maxFileSizeMb = ref<number>(0)
  const ingestionAvailable = ref(false)
  const reasoningAvailable = ref(false)
  const appVersion = ref<string>(__APP_VERSION__)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const context = computed<FeatureFlagContext>(() => ({
    engine: engine.value,
    deploymentMode: deploymentMode.value,
    ingestionAvailable: ingestionAvailable.value,
    reasoningAvailable: reasoningAvailable.value,
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
      deploymentMode.value = data.deploymentMode ?? 'self-hosted'
      maxPageCount.value = data.maxPageCount ?? 0
      maxFileSizeMb.value = data.maxFileSizeMb ?? 0
      ingestionAvailable.value = data.ingestionAvailable ?? false
      reasoningAvailable.value = data.reasoningAvailable ?? false
      appMaxFileSizeMb.value = maxFileSizeMb.value
      appMaxPageCount.value = maxPageCount.value
      if (data.version) appVersion.value = data.version
      loaded.value = true
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load feature flags'
      loaded.value = true
    }
  }

  return {
    engine,
    deploymentMode,
    maxPageCount,
    maxFileSizeMb,
    ingestionAvailable,
    reasoningAvailable,
    appVersion,
    loaded,
    error,
    isEnabled,
    load,
  }
})
