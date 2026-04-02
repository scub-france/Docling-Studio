import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlagStore } from './store'

const mockApiFetch = vi.fn()
vi.mock('../../shared/api/http', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

vi.mock('../settings/store', () => ({
  useSettingsStore: () => ({ apiUrl: 'http://localhost:8000' }),
}))

describe('useFeatureFlagStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockApiFetch.mockReset()
  })

  it('starts unloaded with flags disabled', () => {
    const store = useFeatureFlagStore()
    expect(store.loaded).toBe(false)
    expect(store.isEnabled('chunking')).toBe(false)
  })

  it('enables chunking when engine is local', async () => {
    mockApiFetch.mockResolvedValue({ status: 'ok', engine: 'local' })
    const store = useFeatureFlagStore()
    await store.load()
    expect(store.engine).toBe('local')
    expect(store.loaded).toBe(true)
    expect(store.isEnabled('chunking')).toBe(true)
  })

  it('disables chunking when engine is remote', async () => {
    mockApiFetch.mockResolvedValue({ status: 'ok', engine: 'remote' })
    const store = useFeatureFlagStore()
    await store.load()
    expect(store.engine).toBe('remote')
    expect(store.isEnabled('chunking')).toBe(false)
  })

  it('handles health endpoint failure gracefully', async () => {
    mockApiFetch.mockRejectedValue(new Error('Network error'))
    const store = useFeatureFlagStore()
    await store.load()
    expect(store.loaded).toBe(true)
    expect(store.error).toBe('Network error')
    expect(store.isEnabled('chunking')).toBe(false)
  })
})
