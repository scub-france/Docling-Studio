import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlag } from './useFeatureFlag'
import { useFeatureFlagStore } from './store'

vi.mock('@/shared/api/http', () => ({ apiFetch: vi.fn() }))

describe('useFeatureFlag', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('returns false before flags are loaded', () => {
    const flag = useFeatureFlag('chunking')
    expect(flag.value).toBe(false)
  })

  it('returns reactive value matching store state', () => {
    const store = useFeatureFlagStore()
    store.$patch({ loaded: true, engine: 'local' })

    const flag = useFeatureFlag('chunking')
    expect(flag.value).toBe(true)

    store.$patch({ engine: 'remote' })
    expect(flag.value).toBe(false)
  })
})
