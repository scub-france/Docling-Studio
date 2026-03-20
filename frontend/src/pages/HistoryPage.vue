<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('history.title') }}</h1>
      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: tab === 'analyses' }"
          @click="tab = 'analyses'"
        >{{ t('history.tabAnalyses') }}</button>
        <button
          class="tab-btn"
          :class="{ active: tab === 'documents' }"
          @click="tab = 'documents'"
        >{{ t('history.tabDocuments') }}</button>
      </div>
    </div>
    <div class="page-content">
      <HistoryList v-if="tab === 'analyses'" />
      <div v-else class="doc-tab">
        <div v-if="docStore.documents.length === 0" class="tab-empty">
          {{ t('history.emptyDocs') }}
        </div>
        <div v-else class="doc-items">
          <div
            v-for="doc in docStore.documents"
            :key="doc.id"
            class="doc-row"
          >
            <div class="doc-row-info">
              <svg class="doc-row-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
              </svg>
              <div class="doc-row-meta">
                <span class="doc-row-name">{{ doc.filename }}</span>
                <span class="doc-row-detail">
                  {{ formatSize(doc.fileSize) }}
                  <template v-if="doc.pageCount"> — {{ doc.pageCount }} pages</template>
                  <template v-if="doc.createdAt"> — {{ formatDate(doc.createdAt) }}</template>
                </span>
              </div>
            </div>
            <button class="doc-row-delete" @click="docStore.remove(doc.id)">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { HistoryList, useHistoryStore } from '../features/history/index.js'
import { useDocumentStore } from '../features/document/store.js'
import { useI18n } from '../shared/i18n.js'

const historyStore = useHistoryStore()
const docStore = useDocumentStore()
const { t } = useI18n()
const tab = ref('analyses')

function formatSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / (1024 * 1024)
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

onMounted(() => {
  historyStore.load()
  docStore.load()
})
</script>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.page-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 3px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition);
}

.tab-btn:hover {
  color: var(--text);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page-content {
  flex: 1;
  overflow-y: auto;
}

.tab-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 60px 20px;
  font-size: 14px;
}

.doc-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  transition: background var(--transition);
}

.doc-row:hover { background: var(--bg-hover); }

.doc-row-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.doc-row-icon {
  width: 18px;
  height: 18px;
  color: var(--accent);
  flex-shrink: 0;
}

.doc-row-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.doc-row-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-row-detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  font-family: 'IBM Plex Mono', monospace;
}

.doc-row-delete {
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  color: var(--text-muted);
  border-radius: 4px;
  display: flex;
  opacity: 0;
  transition: all var(--transition);
}

.doc-row:hover .doc-row-delete { opacity: 1; }
.doc-row-delete:hover { color: var(--error); background: rgba(239, 68, 68, 0.1); }
.doc-row-delete svg { width: 16px; height: 16px; }
</style>
