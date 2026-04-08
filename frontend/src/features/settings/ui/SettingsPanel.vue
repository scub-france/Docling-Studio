<template>
  <div class="settings-panel" data-e2e="settings-panel">
    <div class="setting-group">
      <label class="setting-label">{{ t('settings.theme') }}</label>
      <div class="setting-toggle">
        <button :class="{ active: store.theme === 'dark' }" @click="store.setTheme('dark')">
          {{ t('settings.themeDark') }}
        </button>
        <button :class="{ active: store.theme === 'light' }" @click="store.setTheme('light')">
          {{ t('settings.themeLight') }}
        </button>
      </div>
    </div>

    <div class="setting-group">
      <label class="setting-label">{{ t('settings.language') }}</label>
      <div class="setting-toggle">
        <button
          :class="{ active: store.locale === 'fr' }"
          data-e2e="lang-fr"
          @click="store.setLocale('fr')"
        >
          FR
        </button>
        <button
          :class="{ active: store.locale === 'en' }"
          data-e2e="lang-en"
          @click="store.setLocale('en')"
        >
          EN
        </button>
      </div>
    </div>

    <div class="setting-group">
      <label class="setting-label">{{ t('settings.version') }}</label>
      <span class="setting-value">{{ version }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../store'
import { useI18n } from '../../../shared/i18n'

const version = __APP_VERSION__
const store = useSettingsStore()
const { t } = useI18n()
</script>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 320px;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.setting-toggle {
  display: inline-flex;
  gap: 2px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 3px;
  width: fit-content;
}

.setting-toggle button {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: calc(var(--radius-sm) - 2px);
  cursor: pointer;
  transition: all 200ms ease;
}

.setting-toggle button:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

.setting-toggle button.active {
  background: var(--accent-muted);
  color: var(--accent);
  font-weight: 600;
}

.setting-input {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--text);
  font-size: 13px;
  font-family: 'IBM Plex Mono', monospace;
}

.setting-value {
  font-size: 14px;
  color: var(--text);
  font-family: 'IBM Plex Mono', monospace;
}
</style>
