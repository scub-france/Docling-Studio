<template>
  <aside
    v-if="store.hasTrace || store.importDialogOpen"
    class="reasoning-panel"
    data-e2e="reasoning-panel"
  >
    <header class="rp-header">
      <h3>{{ t('reasoning.panelTitle') }}</h3>
      <div class="rp-header-actions">
        <button
          class="rp-btn-ghost rp-btn-toggle"
          :class="{ active: store.focusMode }"
          :aria-pressed="store.focusMode"
          data-e2e="reasoning-focus-toggle"
          :title="t('reasoning.focusHint')"
          @click="store.toggleFocusMode()"
        >
          <span class="rp-dot" />
          {{ t('reasoning.focus') }}
        </button>
        <button class="rp-btn-ghost" @click="store.openImportDialog()">
          {{ t('reasoning.reimport') }}
        </button>
        <button class="rp-btn-ghost" @click="onClear">{{ t('reasoning.clear') }}</button>
      </div>
    </header>

    <section v-if="envelope" class="rp-meta">
      <div v-if="envelope.query" class="rp-query">
        <span class="rp-meta-label">{{ t('reasoning.query') }}</span>
        <span class="rp-meta-value">{{ envelope.query }}</span>
      </div>
      <div class="rp-meta-row">
        <span v-if="envelope.filename" class="rp-meta-chip">{{ envelope.filename }}</span>
        <span v-if="envelope.model?.ollama_name" class="rp-meta-chip">
          {{ envelope.model.ollama_name }}
        </span>
      </div>
    </section>

    <section v-if="result" class="rp-answer">
      <div class="rp-answer-header">
        <span class="rp-converged" :class="{ yes: result.converged, no: !result.converged }">
          {{ result.converged ? t('reasoning.converged') : t('reasoning.notConverged') }}
        </span>
        <span class="rp-stats">
          {{ store.presentCount }} / {{ store.iterations.length }} {{ t('reasoning.resolved') }}
        </span>
      </div>
      <p class="rp-answer-text">{{ result.answer }}</p>
    </section>

    <section v-if="store.missingCount > 0" class="rp-warn" data-e2e="reasoning-missing-warn">
      {{ missingWarning }}
    </section>

    <section class="rp-iterations">
      <h4 class="rp-section-title">{{ t('reasoning.iterationsTitle') }}</h4>
      <div v-if="store.iterations.length === 0" class="rp-empty">
        {{ t('reasoning.noIterations') }}
      </div>
      <div v-else class="rp-iteration-list">
        <IterationCard
          v-for="it in store.iterations"
          :key="it.iteration"
          :iteration="it"
          :active="store.activeIteration === it.iteration"
          @focus="onFocus"
        />
      </div>
    </section>
  </aside>

  <ImportTraceDialog />
</template>

<script setup lang="ts">
import type { Core } from 'cytoscape'
import { computed, watch } from 'vue'

import { useI18n } from '../../../shared/i18n'
import {
  applyReasoningOverlay,
  buildDegradedOverlay,
  clearReasoningOverlay,
  focusIteration,
  nodeIdForSectionRef,
} from '../graphReasoningOverlay'
import { useReasoningStore } from '../store'
import IterationCard from './IterationCard.vue'
import ImportTraceDialog from './ImportTraceDialog.vue'

const props = defineProps<{
  /**
   * The live Cytoscape instance from the GraphView. May be `null` while the
   * graph is loading or if Maintain hasn't been run for this document.
   * Passed down from StudioPage via `graphViewRef.cy`.
   */
  cy: Core | null
}>()

const store = useReasoningStore()
const { t } = useI18n()

const result = computed(() => store.rawResult)
const envelope = computed(() => store.envelope)
const missingWarning = computed(() => {
  // Full miss + no cy → the graph simply isn't loaded. Different message
  // than "N sections are actually missing from the graph".
  if (!props.cy && store.missingCount > 0 && store.presentCount === 0) {
    return t('reasoning.graphNotLoadedWarn')
  }
  return t('reasoning.missingWarn').replace('{n}', String(store.missingCount))
})

function reapplyOverlay(): void {
  if (!store.rawResult) {
    if (props.cy) clearReasoningOverlay(props.cy)
    store.setOverlay(null)
    return
  }
  // When the Cytoscape instance is available (graph loaded for this doc) we
  // run the full overlay: mark visited nodes, draw REASONING_NEXT arrows.
  // Otherwise (404 on the graph endpoint, or Maintain not run yet) we still
  // build the iteration list in "degraded" mode so the user can read the
  // reasoning — they just won't see nodes highlighted.
  const out = props.cy
    ? applyReasoningOverlay(props.cy, store.rawResult, { focusMode: store.focusMode })
    : buildDegradedOverlay(store.rawResult)
  store.setOverlay(out)
}

// Reapply whenever cy, rawResult, or focusMode changes. This handles:
//  - User imports trace after graph loaded (rawResult changes).
//  - User navigates to a different doc which swaps cy (cy changes).
//  - Graph loads AFTER the trace was already imported (cy null → non-null).
//  - User toggles focus mode (focusMode changes) — dim in, dim out.
//  - User clears the trace (rawResult → null → clearReasoningOverlay).
watch(
  () => [props.cy, store.rawResult, store.focusMode] as const,
  () => reapplyOverlay(),
  { immediate: true },
)

function onFocus(iteration: number): void {
  store.setActiveIteration(iteration)
  if (!props.cy) return
  const hit = store.iterations.find((i) => i.iteration === iteration)
  if (!hit || !hit.present) return
  focusIteration(props.cy, nodeIdForSectionRef(hit.sectionRef))
}

function onClear(): void {
  if (props.cy) clearReasoningOverlay(props.cy)
  store.reset()
}
</script>

<style scoped>
.reasoning-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 340px;
  flex: 0 0 340px;
  padding: 16px;
  border-left: 1px solid var(--border);
  background: var(--bg);
  overflow-y: auto;
  height: 100%;
}

.rp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.rp-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.rp-header-actions {
  display: flex;
  gap: 4px;
}

.rp-btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 4px 8px;
  font-size: 11px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
}

.rp-btn-ghost:hover {
  background: var(--border-light);
  color: var(--text);
}

.rp-btn-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.rp-btn-toggle .rp-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border);
  transition: background var(--transition);
}

.rp-btn-toggle.active {
  border-color: #ea580c;
  color: #ea580c;
  background: rgba(234, 88, 12, 0.08);
}

.rp-btn-toggle.active .rp-dot {
  background: #ea580c;
}

.rp-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

.rp-meta-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 2px;
}

.rp-meta-value {
  font-size: 12px;
  color: var(--text);
  line-height: 1.4;
}

.rp-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.rp-meta-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--border-light);
  color: var(--text-secondary);
  font-size: 10px;
  font-family: 'IBM Plex Mono', monospace;
}

.rp-answer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--accent-muted, rgba(234, 88, 12, 0.04));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
}

.rp-answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.rp-converged {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.rp-converged.yes {
  background: rgba(22, 163, 74, 0.15);
  color: #15803d;
}

.rp-converged.no {
  background: rgba(234, 179, 8, 0.15);
  color: #a16207;
}

.rp-stats {
  font-size: 10px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.rp-answer-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
  white-space: pre-wrap;
}

.rp-warn {
  padding: 8px 10px;
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: var(--radius-sm);
  color: #a16207;
  font-size: 12px;
}

.rp-section-title {
  margin: 0 0 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  font-weight: 600;
}

.rp-iteration-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rp-empty {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}
</style>
