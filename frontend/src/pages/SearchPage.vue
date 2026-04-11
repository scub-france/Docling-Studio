<template>
  <div class="search-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('nav.search') }}</h1>
    </div>

    <div v-if="!ingestionStore.available" class="tab-empty">
      {{ t('ingestion.unavailable') }}
    </div>

    <template v-else>
      <div class="chunk-search-bar">
        <input
          v-model="searchInput"
          type="text"
          class="search-input"
          :placeholder="t('ingestion.searchChunks')"
          @keyup.enter="runSearch"
        />
        <div v-if="searchStore.searching" class="spinner-xs" />
      </div>

      <div v-if="searchStore.results.length > 0" class="search-results">
        <div v-for="(result, idx) in searchStore.results" :key="idx" class="search-result-item">
          <div class="result-header">
            <span class="result-filename">{{ result.filename }}</span>
            <span class="result-meta"
              >p.{{ result.pageNumber }} — chunk #{{ result.chunkIndex }}</span
            >
            <span class="result-score">{{ result.score.toFixed(1) }}</span>
          </div>
          <p class="result-content">
            {{ result.content.slice(0, 200) }}{{ result.content.length > 200 ? '…' : '' }}
          </p>
        </div>
      </div>

      <div
        v-if="searchStore.query && !searchStore.searching && searchStore.results.length === 0"
        class="tab-empty"
      >
        {{ t('ingestion.noResults', { q: searchStore.query }) }}
      </div>

      <div v-if="!searchStore.query" class="tab-empty">
        {{ t('search.hint') }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSearchStore } from '../features/search/store'
import { useIngestionStore } from '../features/ingestion/store'
import { useI18n } from '../shared/i18n'

const searchStore = useSearchStore()
const ingestionStore = useIngestionStore()
const { t } = useI18n()

const searchInput = ref('')

function runSearch() {
  if (searchInput.value.trim()) {
    searchStore.search(searchInput.value)
  } else {
    searchStore.clear()
  }
}

onMounted(() => {
  ingestionStore.checkAvailability()
})
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.page-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.tab-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 60px 20px;
  font-size: 14px;
}

/* Chunk search */
.chunk-search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border);
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition);
}

.search-input:focus {
  border-color: var(--accent);
}

.spinner-xs {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Search results */
.search-results {
  flex: 1;
  overflow-y: auto;
}

.search-result-item {
  padding: 10px 24px;
  border-bottom: 1px solid var(--border);
}

.search-result-item:last-child {
  border-bottom: none;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.result-filename {
  font-weight: 600;
  font-size: 13px;
  color: var(--text);
}

.result-meta {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.result-score {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  font-family: 'IBM Plex Mono', monospace;
}

.result-content {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}
</style>
