<template>
  <div class="app-layout">
    <header class="topbar">
      <button class="burger-btn" @click="sidebarOpen = !sidebarOpen" :title="sidebarOpen ? t('nav.collapse') : t('nav.expand')">
        <svg viewBox="0 0 20 20" fill="currentColor" class="burger-icon">
          <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
        </svg>
      </button>
      <div class="topbar-logo">
        <span class="topbar-logo-icon">D</span>
        <span class="topbar-logo-text">Docling Studio</span>
      </div>
      <div class="topbar-spacer" />
      <button class="new-analysis-btn" @click="newAnalysis">
        <svg viewBox="0 0 20 20" fill="currentColor" class="new-analysis-icon"><path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/></svg>
        {{ t('topbar.newAnalysis') }}
      </button>
    </header>

    <div class="app-body">
      <AppSidebar :open="sidebarOpen" />
      <main class="main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { AppSidebar } from '../shared/ui/index'
import { useSettingsStore } from '../features/settings/store'
import { useDocumentStore } from '../features/document/store'
import { useI18n } from '../shared/i18n'

useSettingsStore()
const { t } = useI18n()
const router = useRouter()
const documentStore = useDocumentStore()

const sidebarOpen = ref(true)

function newAnalysis() {
  documentStore.selectedId = null
  router.push('/studio')
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500&display=swap');

:root {
  /* Dark mode palette - MistralAI Studio inspired */
  --bg: #0A0A0B;
  --bg-surface: #111113;
  --bg-elevated: #1A1A1D;
  --bg-hover: #222226;

  --accent: #F97316;
  --accent-hover: #FB923C;
  --accent-muted: rgba(249, 115, 22, 0.15);

  --text: #ECECEF;
  --text-secondary: #A1A1AA;
  --text-muted: #63636E;

  --border: #27272A;
  --border-light: #3F3F46;

  --success: #22C55E;
  --error: #EF4444;
  --warning: #EAB308;
  --info: #3B82F6;

  --radius: 8px;
  --radius-sm: 6px;
  --radius-lg: 12px;

  --sidebar-width: 240px;
  --topbar-height: 48px;
  --transition: 150ms ease;
}

html.light {
  --bg: #FAFAFA;
  --bg-surface: #FFFFFF;
  --bg-elevated: #F4F4F5;
  --bg-hover: #E4E4E7;

  --accent: #F97316;
  --accent-hover: #EA580C;
  --accent-muted: rgba(249, 115, 22, 0.10);

  --text: #18181B;
  --text-secondary: #52525B;
  --text-muted: #A1A1AA;

  --border: #E4E4E7;
  --border-light: #D4D4D8;

  --success: #16A34A;
  --error: #DC2626;
  --warning: #CA8A04;
  --info: #2563EB;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.topbar {
  height: var(--topbar-height);
  min-height: var(--topbar-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
}

.burger-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition);
  padding: 0;
}

.burger-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
  border-color: var(--border);
}

.burger-icon {
  width: 18px;
  height: 18px;
}

.topbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-logo-icon {
  width: 26px;
  height: 26px;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  font-weight: 700;
  font-size: 13px;
}

.topbar-logo-text {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
}

.topbar-spacer {
  flex: 1;
}

.new-analysis-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: white;
  background: var(--accent);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
}

.new-analysis-btn:hover {
  background: var(--accent-hover);
}

.new-analysis-icon {
  width: 14px;
  height: 14px;
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
