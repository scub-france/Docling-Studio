import { defineStore } from 'pinia'
import { ref, watch, watchEffect } from 'vue'
import type { Locale, Theme } from '../../shared/types'

export const useSettingsStore = defineStore('settings', () => {
  const apiUrl = ref('http://localhost:8000')
  const theme = ref<Theme>((localStorage.getItem('docling-theme') as Theme) || 'dark')
  const locale = ref<Locale>((localStorage.getItem('docling-locale') as Locale) || 'fr')

  watch(theme, (v) => localStorage.setItem('docling-theme', v))
  watch(locale, (v) => localStorage.setItem('docling-locale', v))

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
