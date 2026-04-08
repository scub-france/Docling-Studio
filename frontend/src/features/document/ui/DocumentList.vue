<template>
  <div class="doc-list" v-if="store.documents.length">
    <div
      v-for="doc in store.documents"
      :key="doc.id"
      class="doc-item"
      data-e2e="doc-item"
      :class="{ selected: store.selectedId === doc.id }"
      @click="store.select(doc.id)"
    >
      <div class="doc-info">
        <svg class="doc-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
            clip-rule="evenodd"
          />
        </svg>
        <div class="doc-meta">
          <span class="doc-name" data-e2e="doc-name">{{ doc.filename }}</span>
          <span class="doc-size"
            >{{ formatSize(doc.fileSize)
            }}{{ doc.pageCount ? ` — ${doc.pageCount} pages` : '' }}</span
          >
        </div>
      </div>
      <button
        class="doc-delete"
        data-e2e="doc-delete"
        @click.stop="store.remove(doc.id)"
        title="Delete"
      >
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDocumentStore } from '../store'
import { formatSize } from '../../../shared/format'
const store = useDocumentStore()
</script>

<style scoped>
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition);
}

.doc-item:hover {
  background: var(--bg-hover);
}

.doc-item.selected {
  background: var(--accent-muted);
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.doc-icon {
  width: 16px;
  height: 16px;
  color: var(--accent);
  flex-shrink: 0;
}

.doc-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-size {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.doc-delete {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--text-muted);
  border-radius: 4px;
  display: flex;
  opacity: 0;
  transition: all var(--transition);
}

.doc-item:hover .doc-delete {
  opacity: 1;
}
.doc-delete:hover {
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
}
.doc-delete svg {
  width: 14px;
  height: 14px;
}
</style>
