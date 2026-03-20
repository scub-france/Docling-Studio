<template>
  <div class="markdown-viewer" v-html="rendered" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useI18n } from '../../../shared/i18n.js'

const props = defineProps({ content: String })
const { t } = useI18n()

const rendered = computed(() => {
  if (!props.content) return `<p class="empty">${t('results.noMarkdown')}</p>`
  return DOMPurify.sanitize(marked.parse(props.content))
})
</script>

<style scoped>
.markdown-viewer {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text);
}

.markdown-viewer :deep(h1),
.markdown-viewer :deep(h2),
.markdown-viewer :deep(h3) {
  color: var(--text);
  margin: 24px 0 12px;
  font-weight: 600;
}

.markdown-viewer :deep(h1) { font-size: 24px; }
.markdown-viewer :deep(h2) { font-size: 20px; }
.markdown-viewer :deep(h3) { font-size: 16px; }

.markdown-viewer :deep(p) { margin: 8px 0; }

.markdown-viewer :deep(code) {
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 13px;
}

.markdown-viewer :deep(pre) {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-viewer :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-viewer :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.markdown-viewer :deep(th),
.markdown-viewer :deep(td) {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
  font-size: 13px;
}

.markdown-viewer :deep(th) {
  background: var(--bg-elevated);
  font-weight: 600;
}

.markdown-viewer :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-sm);
}

.markdown-viewer :deep(.empty) {
  color: var(--text-muted);
  text-align: center;
  padding: 40px;
}
</style>
