<template>
  <div class="rdv-root" data-e2e="reasoning-document-view">
    <div v-if="!pages || pages.length === 0" class="rdv-empty">
      {{ t('reasoning.docNoContent') }}
    </div>
    <StructureViewer
      v-else
      :pages="pages"
      :document-id="docId"
      :visited-by-self-ref="visitedBySelfRef"
      :focused-self-ref="focusedSelfRef"
      :dim-non-visited="reasoningStore.focusMode"
      selectable
      class="rdv-viewer"
      @element-focus="(ref) => emit('elementFocus', ref)"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * PDF rendering of the document (per-page PNG via /api/documents/:id/preview),
 * augmented with reasoning overlays:
 *   - elements visited by the RAG loop get a bold orange stroke + numbered
 *     badge showing the visit order
 *   - the current `focusedSelfRef` (usually driven by a graph-node click
 *     upstream) auto-jumps to the right page and pulses its bbox
 *   - clicking a bbox emits `elementFocus` so the graph can mirror the
 *     selection (bidirectional sync handled in ReasoningWorkspace).
 */
import { computed } from 'vue'

import StructureViewer from '../../analysis/ui/StructureViewer.vue'
import { useAnalysisStore } from '../../analysis/store'
import { useI18n } from '../../../shared/i18n'
import type { Page } from '../../../shared/types'
import { useReasoningStore } from '../store'

const props = defineProps<{
  docId: string
  focusedSelfRef: string | null
}>()
const emit = defineEmits<{ elementFocus: [selfRef: string] }>()

const analysisStore = useAnalysisStore()
const reasoningStore = useReasoningStore()
const { t } = useI18n()

const pages = computed<Page[]>(() => {
  const hit = analysisStore.analyses.find(
    (a) => a.documentId === props.docId && a.status === 'COMPLETED' && a.pagesJson,
  )
  if (!hit?.pagesJson) return []
  try {
    return JSON.parse(hit.pagesJson) as Page[]
  } catch {
    return []
  }
})

const visitedBySelfRef = computed<Map<string, number>>(() => {
  const out = new Map<string, number>()
  for (const it of reasoningStore.iterations) {
    if (!it.present || !it.sectionRef) continue
    if (!out.has(it.sectionRef)) out.set(it.sectionRef, it.iteration)
  }
  return out
})
</script>

<style scoped>
.rdv-root {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  background: var(--bg);
  padding: 16px 20px;
}

.rdv-viewer {
  max-width: 960px;
  margin: 0 auto;
}

.rdv-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
}
</style>
