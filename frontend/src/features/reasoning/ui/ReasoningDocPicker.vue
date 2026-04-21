<template>
  <div class="rp-picker">
    <header class="rp-picker-header">
      <h1 class="rp-picker-title">{{ t('reasoning.pageTitle') }}</h1>
      <p class="rp-picker-subtitle">{{ t('reasoning.pageSubtitle') }}</p>
    </header>

    <section class="rp-picker-upload" data-e2e="reasoning-upload">
      <div
        class="rp-drop"
        :class="{ dragging, uploading }"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
        @click="openFilePicker"
      >
        <input ref="fileInput" type="file" accept=".pdf" hidden @change="onFileSelect" />
        <div v-if="uploading" class="rp-drop-state">
          <div class="spinner" />
          <span>{{ t('reasoning.uploading') }}</span>
        </div>
        <div v-else class="rp-drop-state">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            class="rp-upload-icon"
          >
            <path d="M12 16V4m0 0L8 8m4-4l4 4M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2" />
          </svg>
          <span class="rp-drop-title">{{ t('reasoning.dropPdf') }}</span>
          <span class="rp-drop-sub">{{ t('reasoning.dropPdfHint') }}</span>
        </div>
      </div>
      <p v-if="uploadError" class="rp-upload-error" data-e2e="reasoning-upload-error">
        {{ uploadError }}
      </p>
    </section>

    <section v-if="docsWithAnalysis.length > 0" class="rp-picker-list">
      <h2 class="rp-list-title">{{ t('reasoning.existingDocs') }}</h2>
      <div class="rp-doc-grid">
        <button
          v-for="doc in docsWithAnalysis"
          :key="doc.id"
          class="rp-doc-card"
          :data-e2e="`reasoning-doc-${doc.id}`"
          @click="emit('select', doc.id)"
        >
          <div class="rp-doc-card-icon">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <div class="rp-doc-card-body">
            <div class="rp-doc-name" :title="doc.filename">{{ doc.filename }}</div>
            <div class="rp-doc-meta">
              <span v-if="doc.pageCount">
                {{ t('reasoning.pagesCount').replace('{n}', String(doc.pageCount)) }}
              </span>
              <span class="rp-doc-meta-dot">·</span>
              <span>{{ formatDate(doc.createdAt) }}</span>
            </div>
          </div>
        </button>
      </div>
    </section>
    <p v-else-if="documentStore.documents.length > 0" class="rp-empty-hint">
      {{ t('reasoning.noAnalyzedDocs') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useAnalysisStore } from '../../analysis/store'
import { useDocumentStore } from '../../document/store'
import { useI18n } from '../../../shared/i18n'

const emit = defineEmits<{
  select: [docId: string]
  uploaded: [docId: string]
}>()

const documentStore = useDocumentStore()
const analysisStore = useAnalysisStore()
const { t } = useI18n()

const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const uploading = ref(false)
const uploadError = ref<string | null>(null)

// Docs that have at least one analysis with document_json — the graph can
// be primed for them without a fresh Docling run. Others need analysis
// first (handled by the upload path or the workspace's silent analyze).
const docsWithAnalysis = computed(() => {
  const analyzedDocIds = new Set(
    analysisStore.analyses
      .filter((a) => a.hasDocumentJson && a.status === 'COMPLETED')
      .map((a) => a.documentId),
  )
  return documentStore.documents
    .filter((d) => analyzedDocIds.has(d.id))
    .sort((a, b) => (b.createdAt ?? '').localeCompare(a.createdAt ?? ''))
})

onMounted(async () => {
  // Fetch both lists in parallel — pickers without prior state need them.
  await Promise.all([
    documentStore.documents.length ? Promise.resolve() : documentStore.load(),
    analysisStore.analyses.length ? Promise.resolve() : analysisStore.load(),
  ])
})

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso
  }
}

function openFilePicker(): void {
  fileInput.value?.click()
}

function isPdf(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

async function handleFile(file: File): Promise<void> {
  uploadError.value = null
  if (!isPdf(file)) {
    uploadError.value = t('upload.invalidFormat')
    return
  }
  uploading.value = true
  try {
    const doc = await documentStore.upload(file)
    if (doc) emit('uploaded', doc.id)
  } catch (e) {
    uploadError.value = (e as Error).message || t('upload.uploading')
  } finally {
    uploading.value = false
  }
}

async function onFileSelect(e: Event): Promise<void> {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) await handleFile(file)
  target.value = ''
}

async function onDrop(e: DragEvent): Promise<void> {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await handleFile(file)
}
</script>

<style scoped>
.rp-picker {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 48px max(24px, 6vw);
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}

.rp-picker-header {
  text-align: center;
}

.rp-picker-title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.rp-picker-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
}

.rp-picker-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rp-drop {
  border: 2px dashed var(--border-light);
  border-radius: var(--radius);
  padding: 40px 16px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition);
}

.rp-drop:hover,
.rp-drop.dragging {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.rp-drop.uploading {
  pointer-events: none;
  opacity: 0.7;
}

.rp-drop-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.rp-upload-icon {
  width: 40px;
  height: 40px;
  color: var(--text-muted);
}

.rp-drop-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.rp-drop-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.rp-upload-error {
  margin: 0;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--error, #dc2626);
  background: rgba(220, 38, 38, 0.08);
  border-radius: var(--radius-sm);
}

.rp-list-title {
  margin: 0 0 16px;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  font-weight: 600;
}

.rp-doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.rp-doc-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  color: inherit;
  transition: all var(--transition);
}

.rp-doc-card:hover {
  border-color: var(--accent);
  background: var(--accent-muted);
  transform: translateY(-1px);
}

.rp-doc-card-icon {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-light);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.rp-doc-card-icon svg {
  width: 20px;
  height: 20px;
}

.rp-doc-card-body {
  flex: 1 1 auto;
  min-width: 0;
}

.rp-doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rp-doc-meta {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.rp-doc-meta-dot {
  margin: 0 4px;
}

.rp-empty-hint {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--border-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
