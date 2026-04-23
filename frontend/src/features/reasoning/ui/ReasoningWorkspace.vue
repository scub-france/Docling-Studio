<template>
  <div class="rw-root" data-e2e="reasoning-workspace">
    <header class="rw-topbar">
      <button class="rw-back-btn" data-e2e="reasoning-back" @click="emit('back')">
        ← {{ t('reasoning.changeDoc') }}
      </button>
      <div class="rw-doc-title" :title="docFilename ?? docId">
        {{ docFilename ?? docId }}
      </div>

      <!-- Main-pane toggle: graph vs docling markdown. Overlay panel on the
           right stays mounted in both modes so the iteration list keeps
           living context — only the main pane swaps. -->
      <div class="rw-mode-switch" role="tablist" :aria-label="t('reasoning.modeSwitchLabel')">
        <button
          type="button"
          role="tab"
          class="rw-mode-btn"
          :class="{ active: mode === 'graph' }"
          :aria-selected="mode === 'graph'"
          data-e2e="reasoning-mode-graph"
          @click="mode = 'graph'"
        >
          {{ t('reasoning.modeGraph') }}
        </button>
        <button
          type="button"
          role="tab"
          class="rw-mode-btn"
          :class="{ active: mode === 'document' }"
          :aria-selected="mode === 'document'"
          data-e2e="reasoning-mode-document"
          @click="mode = 'document'"
        >
          {{ t('reasoning.modeDocument') }}
        </button>
      </div>

      <button
        class="rw-action-btn rw-action-ghost"
        data-e2e="reasoning-workspace-import"
        @click="reasoningStore.openImportDialog()"
      >
        {{ t('reasoning.importBtn') }}
      </button>
      <button
        class="rw-action-btn"
        data-e2e="reasoning-workspace-run"
        @click="reasoningStore.openRunDialog()"
      >
        {{ t('reasoning.runBtn') }}
      </button>
    </header>

    <div class="rw-body">
      <!-- Keep GraphView mounted via v-show rather than v-if so the Cytoscape
           instance + its layout state survive a toggle to document mode and
           back — rebuilding is expensive and would reset pan/zoom. -->
      <GraphView
        v-show="mode === 'graph'"
        ref="graphViewRef"
        :doc-id="docId"
        :fetcher="fetchReasoningGraph"
        @node-focus="onGraphNodeFocus"
      />
      <!-- v-show (not v-if) so the StructureViewer's scroll-to-focused watch
           sees transitions from null → sectionRef that happen while we're in
           graph mode. Otherwise the viewer mounts with an already-set prop
           and the initial scroll never fires. -->
      <DocumentView
        v-show="mode === 'document'"
        :doc-id="docId"
        :focused-self-ref="focusedSelfRef"
        @element-focus="onPdfElementFocus"
      />
      <ReasoningPanel :cy="graphCy" />
    </div>

    <RunReasoningDialog :doc-id="docId" :doc-filename="docFilename" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import GraphView from '../../analysis/ui/GraphView.vue'
import { useI18n } from '../../../shared/i18n'
import { fetchReasoningGraph } from '../api'
import { useReasoningStore } from '../store'
import DocumentView from './DocumentView.vue'
import ReasoningPanel from './ReasoningPanel.vue'
import RunReasoningDialog from './RunReasoningDialog.vue'

type WorkspaceMode = 'graph' | 'document'

const props = defineProps<{
  docId: string
  docFilename?: string | null
}>()

const emit = defineEmits<{ back: [] }>()

const { t } = useI18n()
const reasoningStore = useReasoningStore()

const graphViewRef = ref<InstanceType<typeof GraphView> | null>(null)
const graphCy = computed(() => graphViewRef.value?.cy ?? null)

const mode = ref<WorkspaceMode>('graph')

// Shared focused element (Docling self_ref like "#/texts/12") — the one
// bridge between graph and PDF. Clicking a node in the graph sets this,
// clicking a bbox in the PDF sets this. When set, both views highlight
// the corresponding element. Persists across mode toggles so jumping from
// Graph → Document preserves the currently-looked-at element.
const focusedSelfRef = ref<string | null>(null)

function onGraphNodeFocus(selfRef: string | null): void {
  focusedSelfRef.value = selfRef
}

function onPdfElementFocus(selfRef: string): void {
  focusedSelfRef.value = selfRef
  // Mirror the selection on the graph side — if the user switches back to
  // graph mode, they'll see the same element selected + centered.
  graphViewRef.value?.selectBySelfRef(selfRef)
}

// Click on an iteration card in the reasoning panel flows through
// `reasoningStore.setActiveIteration(n)`. That path already focuses the
// cytoscape node (in ReasoningPanel.onFocus); we mirror it into the PDF
// viewer by resolving the active iteration's section_ref and piping it
// into our shared focus. Done at the workspace level — not inside the
// panel — because the panel doesn't know it has a PDF sibling.
watch(
  () => reasoningStore.activeIteration,
  (n) => {
    if (n === null) return
    const hit = reasoningStore.iterations.find((i) => i.iteration === n)
    if (!hit?.present || !hit.sectionRef) return
    // Flip via null so StructureViewer's watch on `focusedSelfRef` re-fires
    // even when clicking the same iteration twice (same sectionRef).
    focusedSelfRef.value = null
    focusedSelfRef.value = hit.sectionRef
  },
)

// Reset the reasoning store when switching docs — a trace imported for one
// document is meaningless on another. The main-pane mode resets too so a
// new doc opens on the graph (consistent default).
watch(
  () => props.docId,
  () => {
    reasoningStore.reset()
    mode.value = 'graph'
    focusedSelfRef.value = null
  },
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

/* Secondary action next to the primary Run button — import is a rarer path. */
.rw-action-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.rw-action-ghost:hover {
  background: var(--border-light);
  color: var(--text);
  filter: none;
}

/* Segmented control for the main-pane mode (graph vs document). Sits
 * between the doc title and the action buttons. */
.rw-mode-switch {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.rw-mode-btn {
  background: transparent;
  border: 0;
  padding: 5px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.rw-mode-btn + .rw-mode-btn {
  border-left: 1px solid var(--border);
}

.rw-mode-btn:hover:not(.active) {
  background: var(--border-light);
  color: var(--text);
}

.rw-mode-btn.active {
  background: var(--accent);
  color: #fff;
  font-weight: 500;
}

.rw-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.rw-body > :deep(.graph-view),
.rw-body > :deep(.rdv-root) {
  flex: 1 1 auto;
  min-width: 0;
}
</style>
