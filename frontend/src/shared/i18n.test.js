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

  it('has history tab keys in French', () => {
    useSettingsStore.mockReturnValue({ locale: 'fr' })

    const { t } = useI18n()
    expect(t('history.tabAnalyses')).toBe('Analyses')
    expect(t('history.tabDocuments')).toBe('Documents')
    expect(t('history.emptyDocs')).toBe('Aucun document. Importez un document depuis le Studio.')
  })

  it('has history tab keys in English', () => {
    useSettingsStore.mockReturnValue({ locale: 'en' })

    const { t } = useI18n()
    expect(t('history.tabAnalyses')).toBe('Analyses')
    expect(t('history.tabDocuments')).toBe('Documents')
    expect(t('history.emptyDocs')).toBe('No documents yet. Upload a document from the Studio.')
  })

  it('has detailed pipeline option hints in French', () => {
    useSettingsStore.mockReturnValue({ locale: 'fr' })

    const { t } = useI18n()
    // Hints should be longer than simple labels
    expect(t('config.ocrHint').length).toBeGreaterThan(40)
    expect(t('config.tableStructureHint').length).toBeGreaterThan(40)
    expect(t('config.codeEnrichmentHint').length).toBeGreaterThan(40)
    expect(t('config.formulaEnrichmentHint').length).toBeGreaterThan(40)
    expect(t('config.pictureClassificationHint').length).toBeGreaterThan(40)
    expect(t('config.pictureDescriptionHint').length).toBeGreaterThan(40)
    expect(t('config.generatePictureImagesHint').length).toBeGreaterThan(40)
    expect(t('config.generatePageImagesHint').length).toBeGreaterThan(40)
  })

  it('has detailed pipeline option hints in English', () => {
    useSettingsStore.mockReturnValue({ locale: 'en' })

    const { t } = useI18n()
    expect(t('config.ocrHint').length).toBeGreaterThan(40)
    expect(t('config.tableStructureHint').length).toBeGreaterThan(40)
    expect(t('config.codeEnrichmentHint').length).toBeGreaterThan(40)
    expect(t('config.formulaEnrichmentHint').length).toBeGreaterThan(40)
    expect(t('config.pictureClassificationHint').length).toBeGreaterThan(40)
    expect(t('config.pictureDescriptionHint').length).toBeGreaterThan(40)
    expect(t('config.generatePictureImagesHint').length).toBeGreaterThan(40)
    expect(t('config.generatePageImagesHint').length).toBeGreaterThan(40)
  })
})
