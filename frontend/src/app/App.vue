<template>
  <div class="app-layout">
    <AppSidebar />
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { AppSidebar } from '../shared/ui/index.js'
import { useSettingsStore } from '../features/settings/store.js'

useSettingsStore()
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
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  height: 100vh;
}

.main {
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
