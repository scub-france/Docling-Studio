<template>
  <aside class="sidebar" data-e2e="sidebar" :class="{ open }">
    <nav class="sidebar-nav">
      <RouterLink
        to="/"
        class="nav-item"
        data-e2e="nav-home"
        :class="{ active: route.name === 'home' }"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"
          />
        </svg>
        <span class="nav-label">{{ t('nav.home') }}</span>
      </RouterLink>

      <RouterLink
        to="/studio"
        class="nav-item"
        data-e2e="nav-studio"
        :class="{ active: route.name === 'studio' }"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838l-2.727 1.17 1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zm5.99 7.176A9.026 9.026 0 007 15.96v-4.5l.61.26a2.5 2.5 0 001.98 0l.61-.26v4.5a9.026 9.026 0 00-1.7.613z"
          />
        </svg>
        <span class="nav-label">{{ t('nav.studio') }}</span>
      </RouterLink>

      <RouterLink
        to="/documents"
        class="nav-item"
        data-e2e="nav-documents"
        :class="{ active: route.name === 'documents' }"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
            clip-rule="evenodd"
          />
        </svg>
        <span class="nav-label">{{ t('nav.documents') }}</span>
      </RouterLink>

      <RouterLink
        to="/history"
        class="nav-item"
        data-e2e="nav-history"
        :class="{ active: route.name === 'history' }"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
            clip-rule="evenodd"
          />
        </svg>
        <span class="nav-label">{{ t('nav.history') }}</span>
      </RouterLink>

      <RouterLink
        to="/settings"
        class="nav-item"
        data-e2e="nav-settings"
        :class="{ active: route.name === 'settings' }"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
            clip-rule="evenodd"
          />
        </svg>
        <span class="nav-label">{{ t('nav.settings') }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <a
        class="github-badge"
        href="https://github.com/scub-france/Docling-Studio"
        target="_blank"
        rel="noopener"
      >
        <img
          src="https://img.shields.io/github/stars/scub-france/Docling-Studio?style=social"
          alt="GitHub Stars"
          height="20"
        />
      </a>
      <span class="version">v{{ version }}</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from '../i18n'

const version = __APP_VERSION__
const route = useRoute()
const { t } = useI18n()

defineProps({
  open: { type: Boolean, default: false },
})
</script>

<style scoped>
.sidebar {
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  width: 0;
  min-width: 0;
  transition:
    width 250ms ease,
    min-width 250ms ease;
}

.sidebar.open {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition);
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-muted);
  color: var(--accent);
}

.nav-icon {
  width: 18px;
  height: 18px;
  min-width: 18px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border);
  white-space: nowrap;
  overflow: hidden;
}

.github-badge {
  display: block;
  margin-bottom: 8px;
  opacity: 0.7;
  transition: opacity var(--transition);
}

.github-badge:hover {
  opacity: 1;
}

.version {
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}
</style>
