<template>
  <div class="rw-root" data-e2e="reasoning-workspace">
    <header class="rw-topbar">
      <button class="rw-back-btn" data-e2e="reasoning-back" @click="emit('back')">
        ← {{ t('reasoning.changeDoc') }}
      </button>
      <div class="rw-doc-title" :title="docFilename ?? docId">
        {{ docFilename ?? docId }}
      </div>
      <button
        class="rw-action-btn"
        data-e2e="reasoning-workspace-import"
        @click="reasoningStore.openImportDialog()"
      >
        {{ t('reasoning.importBtn') }}
      </button>
    </header>

    <div class="rw-body">
      <GraphView ref="graphViewRef" :doc-id="docId" :fetcher="fetchReasoningGraph" />
      <ReasoningPanel :cy="graphCy" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import GraphView from '../../analysis/ui/GraphView.vue'
import { useI18n } from '../../../shared/i18n'
import { fetchReasoningGraph } from '../api'
import { useReasoningStore } from '../store'
import ReasoningPanel from './ReasoningPanel.vue'

const props = defineProps<{
  docId: string
  docFilename?: string | null
}>()

const emit = defineEmits<{ back: [] }>()

const { t } = useI18n()
const reasoningStore = useReasoningStore()

const graphViewRef = ref<InstanceType<typeof GraphView> | null>(null)
const graphCy = computed(() => graphViewRef.value?.cy ?? null)

// Reset the reasoning store when switching docs — a trace imported for one
// document is meaningless on another.
watch(
  () => props.docId,
  () => reasoningStore.reset(),
)

// Clean up so a later navigation back to the workspace starts fresh.
onBeforeUnmount(() => reasoningStore.reset())
</script>

<style scoped>
.rw-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.rw-topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}

.rw-back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 5px 10px;
  font-size: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
}

.rw-back-btn:hover {
  background: var(--border-light);
  color: var(--text);
}

.rw-doc-title {
  flex: 1 1 auto;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rw-action-btn {
  background: var(--accent);
  color: white;
  border: 0;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
}

.rw-action-btn:hover {
  filter: brightness(0.95);
}

.rw-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.rw-body > :deep(.graph-view) {
  flex: 1 1 auto;
  min-width: 0;
}
</style>
