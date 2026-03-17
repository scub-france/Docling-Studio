import { defineStore } from 'pinia'
import { ref, watch, watchEffect } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const apiUrl = ref('http://localhost:8000')
  const theme = ref(localStorage.getItem('docling-theme') || 'dark')
  const locale = ref(localStorage.getItem('docling-locale') || 'fr')

  watch(theme, (v) => localStorage.setItem('docling-theme', v))
  watch(locale, (v) => localStorage.setItem('docling-locale', v))

  watchEffect(() => {
    document.documentElement.classList.toggle('light', theme.value === 'light')
  })

  function setTheme(t) { theme.value = t }
  function setLocale(l) { locale.value = l }

  return { apiUrl, theme, locale, setTheme, setLocale }
})
