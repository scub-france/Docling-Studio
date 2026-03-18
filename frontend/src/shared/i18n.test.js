import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock settings store before importing i18n
vi.mock('../features/settings/store.js', () => ({
  useSettingsStore: vi.fn(),
}))

import { useSettingsStore } from '../features/settings/store.js'
import { useI18n } from './i18n.js'

describe('useI18n', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('returns French translation by default', () => {
    useSettingsStore.mockReturnValue({ locale: 'fr' })

    const { t } = useI18n()
    expect(t('nav.studio')).toBe('Studio')
    expect(t('nav.history')).toBe('Historique')
    expect(t('nav.settings')).toBe('Paramètres')
  })

  it('returns English translation when locale is en', () => {
    useSettingsStore.mockReturnValue({ locale: 'en' })

    const { t } = useI18n()
    expect(t('nav.history')).toBe('History')
    expect(t('nav.settings')).toBe('Settings')
  })

  it('falls back to French when key missing in current locale', () => {
    useSettingsStore.mockReturnValue({ locale: 'de' })

    const { t } = useI18n()
    expect(t('nav.studio')).toBe('Studio')
  })

  it('returns key when not found in any locale', () => {
    useSettingsStore.mockReturnValue({ locale: 'fr' })

    const { t } = useI18n()
    expect(t('unknown.key')).toBe('unknown.key')
  })

  it('interpolates parameters', () => {
    useSettingsStore.mockReturnValue({ locale: 'en' })

    const { t } = useI18n()
    expect(t('results.pageOf', { current: 3, total: 10 })).toBe('Page 3 of 10')
  })

  it('interpolates parameters in French', () => {
    useSettingsStore.mockReturnValue({ locale: 'fr' })

    const { t } = useI18n()
    expect(t('results.pageOf', { current: 1, total: 5 })).toBe('Page 1 sur 5')
  })
})
