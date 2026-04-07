import { computed } from 'vue'
import { useFeatureFlagStore, type FeatureFlag } from './store'

export function useFeatureFlag(flag: FeatureFlag) {
  const store = useFeatureFlagStore()
  return computed(() => store.isEnabled(flag))
}
