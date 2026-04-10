import { defineStore } from 'pinia'
import { ref, watch, watchEffect } from 'vue'
import type { Locale, Theme } from '../../shared/types'
import { appLocale } from '../../shared/appConfig'

function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeSetItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // localStorage unavailable (private browsing, quota exceeded)
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const apiUrl = ref('http://localhost:8000')
  const theme = ref<Theme>((safeGetItem('docling-theme') as Theme) || 'dark')
  const locale = ref<Locale>((safeGetItem('docling-locale') as Locale) || 'fr')

  watch(theme, (v) => safeSetItem('docling-theme', v))
  watch(
    locale,
    (v) => {
      safeSetItem('docling-locale', v)
      appLocale.value = v
    },
    { immediate: true },
  )

  watchEffect(() => {
    document.documentElement.classList.toggle('light', theme.value === 'light')
  })

  function setTheme(t: Theme): void {
    theme.value = t
  }
  function setLocale(l: Locale): void {
    locale.value = l
  }

  return { apiUrl, theme, locale, setTheme, setLocale }
})
