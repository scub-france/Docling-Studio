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
}

export type FeatureFlag = 'chunking' | 'disclaimer'

interface FeatureFlagDef {
  description: string
  isEnabled: (ctx: FeatureFlagContext) => boolean
}

interface FeatureFlagContext {
  engine: ConversionEngine | null
  deploymentMode: DeploymentMode | null
}

const featureRegistry: Record<FeatureFlag, FeatureFlagDef> = {
  chunking: {
    description: 'Document chunking for RAG preparation',
    isEnabled: (ctx) => ctx.engine === 'local',
  },
  disclaimer: {
    description: 'Show shared-instance disclaimer banner',
    isEnabled: (ctx) => ctx.deploymentMode === 'huggingface',
  },
}

export const useFeatureFlagStore = defineStore('feature-flags', () => {
  const engine = ref<ConversionEngine | null>(null)
  const deploymentMode = ref<DeploymentMode | null>(null)
  const maxPageCount = ref<number>(0)
  const maxFileSizeMb = ref<number>(0)
  const appVersion = ref<string>(__APP_VERSION__)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const context = computed<FeatureFlagContext>(() => ({
    engine: engine.value,
    deploymentMode: deploymentMode.value,
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
    appVersion,
    loaded,
    error,
    isEnabled,
    load,
  }
})
