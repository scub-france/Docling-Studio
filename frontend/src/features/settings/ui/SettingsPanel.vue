<template>
  <div class="settings-panel">
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
        <button :class="{ active: store.locale === 'fr' }" @click="store.setLocale('fr')">FR</button>
        <button :class="{ active: store.locale === 'en' }" @click="store.setLocale('en')">EN</button>
      </div>
    </div>

    <div class="setting-group">
      <label class="setting-label">{{ t('settings.version') }}</label>
      <span class="setting-value">0.1.0</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../store'
import { useI18n } from '../../../shared/i18n'

const store = useSettingsStore()
const { t } = useI18n()
</script>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 500px;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.setting-toggle {
  display: flex;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.setting-toggle button {
  flex: 1;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--transition);
}

.setting-toggle button:hover {
  color: var(--text);
  background: var(--bg-hover);
}

.setting-toggle button.active {
  background: var(--accent-muted);
  color: var(--accent);
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
