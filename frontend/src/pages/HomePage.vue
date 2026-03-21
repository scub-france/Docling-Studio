<template>
  <div class="home-page">
    <div class="home-center">
      <div class="hero">
        <div class="hero-icon">
          <span class="hero-d">D</span>
        </div>
        <h1 class="hero-title">{{ t('home.title') }}</h1>
        <p class="hero-subtitle">{{ t('home.subtitle') }}</p>
      </div>

      <!-- Quick upload -->
      <div class="home-upload">
        <DocumentUpload />
      </div>

      <!-- Stats -->
      <div class="home-stats" v-if="docCount > 0 || analysisCount > 0">
        <div class="stat-card" @click="$router.push('/documents')">
          <div class="stat-value">{{ docCount }}</div>
          <div class="stat-label">{{ t('home.documents') }}</div>
        </div>
        <div class="stat-card" @click="$router.push('/history')">
          <div class="stat-value">{{ analysisCount }}</div>
          <div class="stat-label">{{ t('home.analyses') }}</div>
        </div>
      </div>

      <!-- Recent documents -->
      <div class="home-recent" v-if="documentStore.documents.length > 0">
        <label class="section-label">{{ t('home.recentDocs') }}</label>
        <div class="recent-list">
          <button
            v-for="doc in recentDocs"
            :key="doc.id"
            class="recent-item"
            @click="openInStudio(doc)"
          >
            <svg class="recent-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
            </svg>
            <div class="recent-meta">
              <span class="recent-name">{{ doc.filename }}</span>
              <span class="recent-detail">{{ doc.pageCount ? doc.pageCount + ' pages' : '' }}</span>
            </div>
            <svg class="recent-arrow" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore } from '../features/document/store'
import { useHistoryStore } from '../features/history/index'
import { DocumentUpload } from '../features/document/index'
import { useI18n } from '../shared/i18n'
import type { Document } from '../shared/types'

const router = useRouter()
const documentStore = useDocumentStore()
const historyStore = useHistoryStore()
const { t } = useI18n()

const docCount = computed(() => documentStore.documents.length)
const analysisCount = computed(() => historyStore.analyses.length)
const recentDocs = computed(() => documentStore.documents.slice(0, 5))

function openInStudio(doc: Document) {
  documentStore.select(doc.id)
  router.push('/studio')
}

onMounted(() => {
  documentStore.load()
  historyStore.load()
})
</script>

<style scoped>
.home-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  overflow-y: auto;
}

.home-center {
  max-width: 520px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

/* Hero */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.hero-icon {
  margin-bottom: 4px;
}

.hero-d {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: var(--accent);
  color: white;
  border-radius: var(--radius-lg);
  font-weight: 700;
  font-size: 26px;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.hero-subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  max-width: 400px;
  line-height: 1.6;
}

/* Upload */
.home-upload {
  width: 100%;
}

/* Stats */
.home-stats {
  display: flex;
  gap: 16px;
  width: 100%;
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
}

.stat-card:hover {
  border-color: var(--border-light);
  background: var(--bg-elevated);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
  font-family: 'IBM Plex Mono', monospace;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}

/* Recent docs */
.home-recent {
  width: 100%;
}

.section-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
  text-align: left;
  width: 100%;
  color: inherit;
}

.recent-item:hover {
  background: var(--bg-surface);
  border-color: var(--border);
}

.recent-icon {
  width: 16px;
  height: 16px;
  color: var(--accent);
  flex-shrink: 0;
}

.recent-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.recent-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-detail {
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.recent-arrow {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition);
}

.recent-item:hover .recent-arrow {
  opacity: 1;
}
</style>
