<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('history.title') }}</h1>
    </div>
    <div class="page-content">
      <HistoryList />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { HistoryList, useHistoryStore } from '../features/history/index.js'
import { useI18n } from '../shared/i18n.js'

const store = useHistoryStore()
const { t } = useI18n()
onMounted(() => store.load())
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
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.page-content {
  flex: 1;
  overflow-y: auto;
}
</style>
