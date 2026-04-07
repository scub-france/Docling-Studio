<template>
  <div v-if="pageCount > 1" class="pagination-bar">
    <div class="pagination-nav">
      <button class="pagination-btn" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
        <svg viewBox="0 0 20 20" fill="currentColor" class="pagination-icon">
          <path
            fill-rule="evenodd"
            d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
            clip-rule="evenodd"
          />
        </svg>
      </button>

      <span class="pagination-info">
        {{ t('pagination.pageOf', { current: String(page), total: String(pageCount) }) }}
      </span>

      <button
        class="pagination-btn"
        :disabled="page >= pageCount"
        @click="$emit('update:page', page + 1)"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" class="pagination-icon">
          <path
            fill-rule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>

    <div class="pagination-size">
      <select
        :value="pageSize"
        class="pagination-select"
        @change="$emit('update:pageSize', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="size in pageSizeOptions" :key="size" :value="size">
          {{ size }} {{ t('pagination.perPage') }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n'

defineProps<{
  page: number
  pageCount: number
  pageSize: number
}>()

defineEmits<{
  'update:page': [value: number]
  'update:pageSize': [value: number]
}>()

const { t } = useI18n()
const pageSizeOptions = [5, 10, 20, 50]
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  gap: 8px;
  flex-shrink: 0;
}

.pagination-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s;
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.pagination-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.pagination-icon {
  width: 14px;
  height: 14px;
}

.pagination-info {
  font-size: 12px;
  color: var(--text-muted);
  padding: 0 6px;
  white-space: nowrap;
}

.pagination-size {
  flex-shrink: 0;
}

.pagination-select {
  font-size: 11px;
  padding: 3px 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text-muted);
  cursor: pointer;
}

.pagination-select:hover {
  border-color: var(--accent);
}
</style>
