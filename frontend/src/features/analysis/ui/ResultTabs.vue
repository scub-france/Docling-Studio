<template>
  <div class="result-tabs" v-if="store.currentAnalysis?.status === 'COMPLETED'">
    <div class="tabs-header">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Page chip -->
    <div class="page-indicator" v-if="totalPages > 0">
      <span class="page-chip">{{ t('results.pageOf', { current: currentPage, total: totalPages }) }}</span>
    </div>

    <div class="tab-content">
      <MarkdownViewer v-if="activeTab === 'text'" :content="pageMarkdown" />
      <div v-else-if="activeTab === 'markdown'" class="raw-markdown">
        <pre class="raw-content">{{ pageMarkdown }}</pre>
      </div>
      <ImageGallery v-else-if="activeTab === 'images'" :pages="currentPageAsArray" />
    </div>
  </div>
  <div v-else-if="store.currentAnalysis?.status === 'RUNNING'" class="result-placeholder">
    <div class="spinner-large" />
    <span>{{ t('studio.analysisRunning') }}</span>
  </div>
  <div v-else-if="store.currentAnalysis?.status === 'FAILED'" class="result-placeholder error">
    <svg viewBox="0 0 20 20" fill="currentColor" class="error-icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
    <span>{{ store.currentAnalysis.errorMessage || t('results.analysisFailed') }}</span>
  </div>
  <div v-else class="result-placeholder">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
      <path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v16.5c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9zm3.75 11.625a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
    </svg>
    <span>{{ t('results.runAnalysis') }}</span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAnalysisStore } from '../store.js'
import MarkdownViewer from './MarkdownViewer.vue'
import ImageGallery from './ImageGallery.vue'
import { useI18n } from '../../../shared/i18n.js'

const props = defineProps({
  currentPage: { type: Number, default: 1 }
})

const store = useAnalysisStore()
const { t } = useI18n()
const activeTab = ref('text')

const tabs = computed(() => [
  { id: 'text', label: t('results.textResult') },
  { id: 'markdown', label: t('results.markdown') },
  { id: 'images', label: t('results.images') }
])

const totalPages = computed(() => store.currentPages.length)

const currentPageData = computed(() => {
  return store.currentPages.find(p => p.page_number === props.currentPage) || null
})

const currentPageAsArray = computed(() => {
  return currentPageData.value ? [currentPageData.value] : []
})

/** Build markdown content from page elements */
const pageMarkdown = computed(() => {
  const page = currentPageData.value
  if (!page) return ''

  return (page.elements || [])
    .map(el => formatElement(el))
    .filter(Boolean)
    .join('\n\n')
})

function formatElement(el) {
  if (!el.content) return ''
  const indent = '  '.repeat(Math.max(0, (el.level || 0) - 1))
  switch (el.type) {
    case 'title':
      return `# ${el.content}`
    case 'section_header': {
      // Use hierarchy level for heading depth (h2-h4)
      const depth = Math.min(Math.max(el.level || 2, 2), 4)
      return `${'#'.repeat(depth)} ${el.content}`
    }
    case 'caption':
      return `${indent}*${el.content}*`
    case 'table':
      return el.content
    case 'formula':
      return `${indent}$$${el.content}$$`
    case 'code':
      return `${indent}\`\`\`\n${el.content}\n\`\`\``
    case 'list':
      return `${indent}- ${el.content}`
    default:
      return `${indent}${el.content}`
  }
}
</script>

<style scoped>
.result-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.tabs-header {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  padding: 0 16px;
  flex-shrink: 0;
  background: var(--bg);
}

.tab-btn {
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
}

.tab-btn:hover { color: var(--text-secondary); }
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.page-indicator {
  padding: 8px 16px;
  flex-shrink: 0;
}

.page-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-muted);
  padding: 3px 10px;
  border-radius: 10px;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.raw-markdown {
  height: 100%;
}

.raw-content {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-muted);
  font-size: 14px;
}

.result-placeholder.error { color: var(--error); }
.error-icon { width: 32px; height: 32px; }
.empty-icon { width: 48px; height: 48px; color: var(--border-light); }

.spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
