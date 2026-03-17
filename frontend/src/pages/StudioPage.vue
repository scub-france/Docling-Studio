<template>
  <!-- STATE 1: No document selected — Import view -->
  <div v-if="!selectedDoc" class="import-page">
    <div class="import-center">
      <div class="import-logo">
        <span class="logo-icon">D</span>
      </div>
      <h1 class="import-title">{{ t('studio.title') }}</h1>
      <p class="import-subtitle">{{ t('studio.subtitle') }}</p>
      <DocumentUpload />
      <div class="import-docs" v-if="documentStore.documents.length">
        <label class="section-label">{{ t('studio.recentDocs') }}</label>
        <DocumentList />
      </div>
    </div>
  </div>

  <!-- STATE 2 & 3: Document selected — Configurer / V&eacute;rifier -->
  <div v-else class="studio-page">
    <!-- Top bar -->
    <div class="studio-topbar">
      <div class="topbar-left">
        <h1 class="topbar-title">{{ t('studio.title') }}</h1>
        <div class="mode-toggle">
          <button
            class="toggle-btn"
            :class="{ active: mode === 'configurer' }"
            @click="mode = 'configurer'"
          >{{ t('studio.configure') }}</button>
          <button
            class="toggle-btn"
            :class="{ active: mode === 'verifier' }"
            @click="mode = 'verifier'"
            :disabled="!analysisStore.currentAnalysis"
          >{{ t('studio.verify') }}</button>
        </div>
      </div>
      <div class="topbar-actions">
        <button class="topbar-btn" @click="addMore">
          <svg viewBox="0 0 20 20" fill="currentColor" class="btn-icon"><path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/></svg>
          {{ t('studio.addFiles') }}
        </button>
        <button
          class="topbar-btn primary"
          :disabled="analysisStore.running"
          @click="runAnalysis"
          v-if="mode === 'configurer'"
        >
          <div v-if="analysisStore.running" class="spinner-sm" />
          <svg v-else viewBox="0 0 20 20" fill="currentColor" class="btn-icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/></svg>
          {{ analysisStore.running ? t('studio.analyzing') : t('studio.run') }}
        </button>
      </div>
    </div>

    <!-- Document info bar -->
    <div class="doc-infobar">
      <div class="doc-info-left">
        <svg class="doc-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/></svg>
        <span class="doc-filename">{{ selectedDoc.filename }}</span>
        <span class="doc-status-chip loaded">{{ t('studio.loaded') }}</span>
      </div>
      <div class="doc-info-right" v-if="analysisStore.currentAnalysis">
        <span class="info-badge" v-if="analysisStore.currentAnalysis.status === 'COMPLETED'">
          <span class="info-dot success" />
          {{ selectedDoc.pageCount || '?' }} pages
        </span>
        <span class="info-badge" v-if="analysisStore.currentAnalysis.status === 'RUNNING'">
          <div class="spinner-xs" />
          {{ t('studio.analysisRunning') }}
        </span>
        <span class="info-badge error" v-if="analysisStore.currentAnalysis.status === 'FAILED'">
          <span class="info-dot error" />
          {{ t('studio.failed') }}
        </span>
      </div>
    </div>

    <!-- Main content area -->
    <div class="studio-main">
      <!-- Left: PDF Viewer -->
      <div class="pdf-viewer-panel">
        <div class="pdf-nav-bar">
          <button class="pdf-nav-btn" :disabled="currentPage <= 1" @click="currentPage--">
            <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
          </button>
          <div class="pdf-page-input-wrap">
            <input
              type="number"
              class="pdf-page-input"
              :value="currentPage"
              @change="onPageInput"
              min="1"
              :max="selectedDoc.pageCount || 1"
            />
          </div>
          <span class="pdf-page-total">/ {{ selectedDoc.pageCount || '?' }}</span>
          <button class="pdf-nav-btn" :disabled="!selectedDoc.pageCount || currentPage >= selectedDoc.pageCount" @click="currentPage++">
            <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
          </button>
          <span class="pdf-separator" />
          <span class="pdf-zoom">100%</span>
          <template v-if="hasAnalysisResults">
            <span class="pdf-separator" />
            <button
              class="visual-toggle"
              :class="{ active: visualMode }"
              @click="visualMode = !visualMode"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" class="btn-icon"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
              {{ t('studio.visual') }}
            </button>
          </template>
        </div>
        <div class="pdf-image-area">
          <div class="pdf-image-wrapper">
            <img
              v-if="previewUrl"
              ref="pdfImageRef"
              :src="previewUrl"
              :alt="`Page ${currentPage}`"
              class="pdf-image"
              @load="onPdfImageLoad"
            />
            <BboxOverlay
              v-if="visualMode && hasAnalysisResults"
              ref="bboxOverlayRef"
              :image-el="pdfImageRef"
              :page-data="currentPageData"
            />
          </div>
        </div>
      </div>

      <!-- Right: Config or Results panel -->
      <div class="right-panel">
        <!-- CONFIGURER MODE -->
        <div v-if="mode === 'configurer'" class="config-panel">
          <div class="config-section">
            <label class="config-label">
              {{ t('config.model') }}
              <span class="config-hint">?</span>
            </label>
            <div class="config-select-display">
              <span class="config-model-name">Docling</span>
              <span class="config-model-sub">docling-latest</span>
            </div>
          </div>

          <div class="config-section">
            <label class="config-label">
              {{ t('config.pages') }}
              <span class="config-hint">?</span>
            </label>
            <input type="text" class="config-input" :placeholder="t('config.pagesPlaceholder')" v-model="pageRange" />
          </div>

          <div class="config-section">
            <label class="config-label">
              {{ t('config.extractTables') }}
              <span class="config-hint">?</span>
            </label>
            <select class="config-select" v-model="tableMode">
              <option value="markdown">{{ t('config.markdownIntegrated') }}</option>
              <option value="html">HTML</option>
              <option value="csv">CSV</option>
            </select>
          </div>

          <div class="config-section">
            <label class="config-label">{{ t('config.extract') }}</label>
            <div class="extract-options">
              <button
                v-for="opt in extractOptions"
                :key="opt.id"
                class="extract-btn"
                :class="{ active: activeExtracts.has(opt.id) }"
                @click="toggleExtract(opt.id)"
              >
                <svg v-if="opt.icon === 'image'" viewBox="0 0 20 20" fill="currentColor" class="extract-icon"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/></svg>
                <svg v-else-if="opt.icon === 'header'" viewBox="0 0 20 20" fill="currentColor" class="extract-icon"><path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/></svg>
                <svg v-else viewBox="0 0 20 20" fill="currentColor" class="extract-icon"><path d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm0 2h10v7h-2l-1-2-3 4-2-3-2 3V5z"/></svg>
                {{ opt.label }}
              </button>
            </div>
          </div>

          <div class="config-section">
            <label class="config-label">
              {{ t('config.annotateImages') }}
              <span class="config-hint">?</span>
            </label>
            <button class="config-add-btn">{{ t('config.add') }}</button>
          </div>

          <!-- Documents list at bottom -->
          <div class="config-section config-docs">
            <label class="config-label">{{ t('config.documents') }}</label>
            <DocumentList />
          </div>
        </div>

        <!-- VERIFIER MODE -->
        <div v-if="mode === 'verifier'" class="verify-panel">
          <ResultTabs :current-page="currentPage" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, reactive } from 'vue'
import { useDocumentStore } from '../features/document/store.js'
import { useAnalysisStore } from '../features/analysis/store.js'
import { DocumentUpload, DocumentList } from '../features/document/index.js'
import { ResultTabs } from '../features/analysis/index.js'
import BboxOverlay from '../features/analysis/ui/BboxOverlay.vue'
import { getPreviewUrl } from '../features/document/api.js'
import { useI18n } from '../shared/i18n.js'

const documentStore = useDocumentStore()
const analysisStore = useAnalysisStore()
const { t } = useI18n()

const mode = ref('configurer')
const currentPage = ref(1)
const pageRange = ref('')
const tableMode = ref('markdown')
const visualMode = ref(false)
const pdfImageRef = ref(null)
const bboxOverlayRef = ref(null)

const hasAnalysisResults = computed(() => {
  return analysisStore.currentAnalysis?.status === 'COMPLETED' && analysisStore.currentPages?.length > 0
})

const currentPageData = computed(() => {
  if (!analysisStore.currentPages) return null
  return analysisStore.currentPages.find(p => p.page_number === currentPage.value) || null
})

function onPdfImageLoad() {
  nextTick(() => bboxOverlayRef.value?.draw())
}

const extractOptions = computed(() => [
  { id: 'images', label: t('config.images'), icon: 'image' },
  { id: 'header', label: t('config.header'), icon: 'header' },
  { id: 'footer', label: t('config.footer'), icon: 'footer' }
])
const activeExtracts = reactive(new Set(['images']))

function toggleExtract(id) {
  if (activeExtracts.has(id)) activeExtracts.delete(id)
  else activeExtracts.add(id)
}

const selectedDoc = computed(() => {
  return documentStore.documents.find(d => d.id === documentStore.selectedId)
})

const previewUrl = computed(() => {
  if (!selectedDoc.value) return null
  return getPreviewUrl(selectedDoc.value.id, currentPage.value)
})

function onPageInput(e) {
  const val = parseInt(e.target.value)
  if (!val || val < 1) return
  const max = selectedDoc.value?.pageCount || val
  currentPage.value = Math.min(val, max)
}

async function runAnalysis() {
  if (!documentStore.selectedId) return
  await analysisStore.run(documentStore.selectedId)
}

function addMore() {
  documentStore.selectedId = null
}

// Auto-switch to verifier when analysis completes + refresh document data (pageCount)
watch(() => analysisStore.currentAnalysis?.status, (status) => {
  if (status === 'COMPLETED') {
    mode.value = 'verifier'
    documentStore.load()
  }
})

onMounted(() => {
  documentStore.load()
  analysisStore.load()
})
</script>

<style scoped>
/* ===== IMPORT PAGE ===== */
.import-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.import-center {
  max-width: 480px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.import-logo {
  margin-bottom: 8px;
}

.import-logo .logo-icon {
  width: 48px;
  height: 48px;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  font-weight: 700;
  font-size: 22px;
}

.import-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text);
  text-align: center;
}

.import-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 8px;
}

.import-docs {
  width: 100%;
  margin-top: 16px;
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

/* ===== STUDIO PAGE ===== */
.studio-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Top bar */
.studio-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--bg-surface);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.mode-toggle {
  display: flex;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  overflow: hidden;
}

.toggle-btn {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--transition);
}

.toggle-btn:hover:not(:disabled) {
  color: var(--text);
}

.toggle-btn.active {
  background: var(--bg);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.toggle-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.topbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.topbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
}

.topbar-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.topbar-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.topbar-btn.primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.topbar-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.topbar-btn .btn-icon {
  width: 16px;
  height: 16px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* Doc info bar */
.doc-infobar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--bg);
}

.doc-info-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  width: 16px;
  height: 16px;
  color: var(--error);
}

.doc-filename {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
}

.doc-status-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.doc-status-chip.loaded {
  background: rgba(34, 197, 94, 0.15);
  color: var(--success);
}

.doc-info-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: 'IBM Plex Mono', monospace;
}

.info-badge.error {
  color: var(--error);
}

.info-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.info-dot.success { background: var(--success); }
.info-dot.error { background: var(--error); }

.spinner-xs {
  width: 12px;
  height: 12px;
  border: 2px solid var(--border-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* Main content */
.studio-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 380px;
  overflow: hidden;
}

/* PDF Viewer */
.pdf-viewer-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border);
}

.pdf-nav-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--bg-surface);
}

.pdf-nav-btn {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  transition: all var(--transition);
}

.pdf-nav-btn:hover:not(:disabled) { background: var(--bg-hover); color: var(--text); }
.pdf-nav-btn:disabled { opacity: 0.3; cursor: default; }
.pdf-nav-btn svg { width: 16px; height: 16px; }

.pdf-page-input-wrap {
  display: flex;
}

.pdf-page-input {
  width: 40px;
  text-align: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-size: 13px;
  font-family: 'IBM Plex Mono', monospace;
  padding: 3px;
  -moz-appearance: textfield;
}

.pdf-page-input::-webkit-outer-spin-button,
.pdf-page-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.pdf-page-total {
  font-size: 13px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
  margin-right: 8px;
}

.pdf-separator {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 8px;
}

.pdf-zoom {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: 'IBM Plex Mono', monospace;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 10px;
}

.visual-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition);
}

.visual-toggle .btn-icon {
  width: 14px;
  height: 14px;
}

.visual-toggle:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.visual-toggle.active {
  background: var(--accent-muted);
  border-color: var(--accent);
  color: var(--accent);
}

.pdf-image-area {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  background: var(--bg-elevated);
  padding: 20px;
}

.pdf-image-wrapper {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.pdf-image {
  max-width: 100%;
  height: auto;
  display: block;
  box-shadow: 0 2px 20px rgba(0,0,0,0.4);
  border-radius: 2px;
}

/* Right panel */
.right-panel {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

/* Config panel */
.config-panel {
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  font-size: 10px;
  color: var(--text-muted);
  cursor: help;
}

.config-select-display {
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
}

.config-model-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.config-model-sub {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.config-input {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  transition: border-color var(--transition);
}

.config-input::placeholder {
  color: var(--text-muted);
}

.config-input:focus {
  outline: none;
  border-color: var(--accent);
}

.config-select {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23A1A1AA' viewBox='0 0 20 20'%3E%3Cpath fill-rule='evenodd' d='M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z' clip-rule='evenodd'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.config-select:focus {
  outline: none;
  border-color: var(--accent);
}

.config-select option {
  background: var(--bg-surface);
  color: var(--text);
}

.extract-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.extract-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.extract-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.extract-btn.active {
  background: var(--accent-muted);
  border-color: var(--accent);
  color: var(--accent);
}

.extract-icon {
  width: 16px;
  height: 16px;
}

.config-add-btn {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  align-self: flex-start;
}

.config-add-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.config-docs {
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding-top: 16px;
}

/* Verify panel */
.verify-panel {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
