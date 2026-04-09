<template>
  <div class="chunk-panel" data-e2e="chunk-panel">
    <!-- Chunking config — collapsible -->
    <div class="chunk-config">
      <button class="config-toggle" data-e2e="config-toggle" @click="configOpen = !configOpen">
        <svg
          class="config-chevron"
          data-e2e="config-chevron"
          :class="{ open: configOpen }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clip-rule="evenodd"
          />
        </svg>
        <span class="config-label">{{ t('chunking.settings') }}</span>
      </button>

      <div v-if="configOpen" class="config-body" data-e2e="config-body">
        <div class="config-row">
          <label class="config-label-sm">{{ t('chunking.chunkerType') }}</label>
          <select class="config-select" data-e2e="config-select" v-model="options.chunker_type">
            <option value="hybrid">Hybrid</option>
            <option value="hierarchical">Hierarchical</option>
          </select>
        </div>

        <div class="config-row">
          <label class="config-label-sm">{{ t('chunking.maxTokens') }}</label>
          <input
            type="number"
            class="config-input"
            data-e2e="config-input"
            v-model.number="options.max_tokens"
            min="64"
            max="8192"
            step="64"
          />
        </div>

        <div class="config-toggle-row" v-if="options.chunker_type === 'hybrid'">
          <label class="toggle-label">
            <input type="checkbox" v-model="options.merge_peers" class="toggle-input" />
            <span class="toggle-switch" />
            <span class="toggle-text">{{ t('chunking.mergePeers') }}</span>
          </label>
        </div>

        <div class="config-toggle-row" v-if="options.chunker_type === 'hybrid'">
          <label class="toggle-label">
            <input type="checkbox" v-model="options.repeat_table_header" class="toggle-input" />
            <span class="toggle-switch" />
            <span class="toggle-text">{{ t('chunking.repeatTableHeader') }}</span>
          </label>
        </div>

        <button
          class="chunk-btn primary"
          data-e2e="chunk-btn"
          :disabled="!canRechunk || analysisStore.rechunking"
          @click="doRechunk"
        >
          <div v-if="analysisStore.rechunking" class="spinner-sm" />
          {{ analysisStore.rechunking ? t('chunking.chunking') : t('chunking.run') }}
        </button>
      </div>
    </div>

    <!-- Chunks list -->
    <div class="chunk-results" data-e2e="chunk-results" v-if="pageChunks.length">
      <div class="chunk-summary" data-e2e="chunk-summary">
        {{ pagination.totalItems.value }} {{ t('chunking.chunks') }}
      </div>
      <div class="chunk-list">
        <div
          class="chunk-card"
          data-e2e="chunk-card"
          v-for="(chunk, localIdx) in pagination.paginatedItems.value"
          :key="globalIndex(localIdx)"
          :class="{ highlighted: hoveredChunkIdx === globalIndex(localIdx) }"
          @mouseenter="onChunkHover(chunk, localIdx)"
          @mouseleave="onChunkLeave"
        >
          <div class="chunk-header">
            <span class="chunk-index" data-e2e="chunk-index">#{{ globalIndex(localIdx) + 1 }}</span>
            <span class="chunk-tokens" data-e2e="chunk-tokens" v-if="chunk.tokenCount">
              {{ chunk.tokenCount }} tokens
            </span>
            <span class="chunk-page" v-if="chunk.sourcePage"> p.{{ chunk.sourcePage }} </span>
          </div>
          <div class="chunk-headings" v-if="chunk.headings.length">
            <span class="chunk-heading" v-for="h in chunk.headings" :key="h">{{ h }}</span>
          </div>
          <div class="chunk-text" data-e2e="chunk-text">{{ chunk.text }}</div>
        </div>
      </div>
    </div>

    <div class="chunk-empty" v-else-if="!analysisStore.rechunking">
      <p>
        {{
          analysisStore.currentChunks.length ? t('chunking.noChunksOnPage') : t('chunking.noChunks')
        }}
      </p>
    </div>

    <!-- Pagination -->
    <PaginationBar
      :page="pagination.page.value"
      :page-count="pagination.pageCount.value"
      :page-size="pagination.pageSize.value"
      @update:page="pagination.goTo($event)"
      @update:page-size="pagination.setPageSize($event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAnalysisStore } from '../../analysis/store'
import { useI18n } from '../../../shared/i18n'
import { usePagination } from '../../../shared/composables/usePagination'
import { PaginationBar } from '../../../shared/ui'
import type { Chunk, ChunkBbox, ChunkingOptions } from '../../../shared/types'

const props = defineProps<{
  currentPage: number
}>()

const emit = defineEmits<{
  'highlight-bboxes': [bboxes: ChunkBbox[]]
}>()

const analysisStore = useAnalysisStore()
const { t } = useI18n()

const configOpen = ref(true)

const options = reactive<Required<ChunkingOptions>>({
  chunker_type: 'hybrid',
  max_tokens: 512,
  merge_peers: true,
  repeat_table_header: true,
})

const canRechunk = computed(() => {
  const analysis = analysisStore.currentAnalysis
  return analysis?.status === 'COMPLETED' && analysis.hasDocumentJson
})

const pageChunks = computed(() =>
  analysisStore.currentChunks.filter((c) => c.sourcePage === props.currentPage),
)
const pagination = usePagination(pageChunks, { pageSize: 20 })

function globalIndex(localIdx: number): number {
  return (pagination.page.value - 1) * pagination.pageSize.value + localIdx
}

const hoveredChunkIdx = ref(-1)

function onChunkHover(chunk: Chunk, localIdx: number) {
  hoveredChunkIdx.value = globalIndex(localIdx)
  const pageBboxes = chunk.bboxes.filter((b) => b.page === props.currentPage)
  emit('highlight-bboxes', pageBboxes)
}

function onChunkLeave() {
  hoveredChunkIdx.value = -1
  emit('highlight-bboxes', [])
}

async function doRechunk() {
  if (!analysisStore.currentAnalysis) return
  await analysisStore.rechunk(analysisStore.currentAnalysis.id, { ...options })
}
</script>

<style scoped>
.chunk-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chunk-config {
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.config-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
}

.config-toggle:hover {
  color: var(--text);
}

.config-chevron {
  width: 14px;
  height: 14px;
  transition: transform 0.2s;
  transform: rotate(0deg);
}

.config-chevron.open {
  transform: rotate(90deg);
}

.config-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.config-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 16px 16px;
}

.config-label-sm {
  font-size: 12px;
  color: var(--text-secondary);
}

.config-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-select,
.config-input {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
  font-size: 13px;
  color: var(--text);
  width: 100%;
}

.config-toggle-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
}

.toggle-input {
  display: none;
}

.toggle-switch {
  width: 32px;
  height: 18px;
  background: var(--bg-tertiary);
  border-radius: 9px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-input:checked + .toggle-switch {
  background: var(--accent);
}

.toggle-input:checked + .toggle-switch::after {
  transform: translateX(14px);
}

.chunk-btn {
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 4px;
}

.chunk-btn.primary {
  background: var(--accent);
  color: white;
}

.chunk-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chunk-results {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.chunk-summary {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chunk-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
  cursor: default;
  transition:
    border-color 0.15s,
    background 0.15s;
}

.chunk-card:hover {
  border-color: #f59e0b;
}

.chunk-card.highlighted {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.chunk-index {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
}

.chunk-tokens,
.chunk-page {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: 4px;
}

.chunk-headings {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.chunk-heading {
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-bg, rgba(99, 102, 241, 0.1));
  padding: 1px 6px;
  border-radius: 4px;
}

.chunk-text {
  font-size: 12px;
  color: var(--text);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}

.chunk-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 13px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
