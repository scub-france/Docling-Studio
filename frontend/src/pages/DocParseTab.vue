<template>
  <div class="parse-tab" data-e2e="parse-tab">
    <LayersBar
      :elements="currentPageElements"
      :hidden-types="hiddenTypes"
      @update:hidden-types="(next) => (hiddenTypes = next)"
    >
      <template #action>
        <button
          type="button"
          class="tab-action-cta"
          :disabled="analysisStore.running"
          :title="t('newAnalysis.title')"
          data-e2e="parse-new-analysis"
          @click="onLaunchAnalysis"
        >
          <span v-if="analysisStore.running" class="tab-action-spinner" />
          <span v-else>+</span>
          {{ analysisStore.running ? t('newAnalysis.running') : t('newAnalysis.title') }}
        </button>
      </template>
    </LayersBar>
    <div v-if="documentStore.workspaceDraftDirty || documentStore.workspaceError" class="parse-banner">
      <p class="parse-banner-text">{{ bannerMessage }}</p>
      <button
        v-if="documentStore.workspaceDraftDirty"
        type="button"
        class="parse-banner-btn"
        data-e2e="parse-discard-local-draft"
        @click="onDiscardLocalDraft"
      >
        {{ t('parse.discardLocalDraft') }}
      </button>
    </div>
    <div class="parse-body">
      <aside class="parse-structure">
        <header class="parse-structure-header">
          <h2 class="parse-structure-title">{{ t('parse.structureTitle') }}</h2>
          <span class="parse-structure-count">
            {{ t('parse.structureNodes', { n: nodeCount }) }}
          </span>
          <div class="parse-structure-actions">
            <button
              type="button"
              class="tree-action-btn"
              :title="t('parse.expandAll')"
              :aria-label="t('parse.expandAll')"
              data-e2e="tree-expand-all"
              @click="onExpandAll"
            >
              ⊕
            </button>
            <button
              type="button"
              class="tree-action-btn"
              :title="t('parse.collapseAll')"
              :aria-label="t('parse.collapseAll')"
              data-e2e="tree-collapse-all"
              @click="onCollapseAll"
            >
              ⊖
            </button>
          </div>
        </header>
        <input
          v-model="filter"
          type="text"
          class="parse-structure-filter"
          :placeholder="t('parse.filterPlaceholder')"
          data-e2e="structure-filter"
        />
        <DocTreeRail
          :key="treeRemountKey"
          :nodes="filteredNodes"
          :loading="documentStore.workspaceLoading"
          :error="documentStore.workspaceError ? null : treeError"
          :selected="selectedNodeRef"
          :highlight="selectedNodeRef"
          :default-open="treeDefaultOpen"
          @select="onTreeSelect"
          @reload="reloadDerivedTree"
        />
      </aside>
      <div class="parse-stage">
        <PagePreviewWithOverlay
          v-if="documentStore.workspacePages.length"
          :document-id="docId"
          :pages="documentStore.workspacePages"
          :current-page="currentPage"
          :hidden-types="hiddenTypes"
          :show-labels="true"
          :highlighted-refs="highlightedRefs"
          @update:current-page="(p) => (currentPage = p)"
          @hover-element="onHoverElement"
          @click-element="onClickElement"
        />
        <div v-else-if="documentStore.workspaceLoading" class="parse-state">
          <span class="spinner" />
        </div>
        <div v-else class="parse-state parse-state--empty">
          <p>{{ t('parse.noAnalysis') }}</p>
        </div>
      </div>
      <ElementProperties
        :element="selectedElement"
        :element-boxes="selectedElementBoxes"
        :page-width="currentPageWidth"
        :page-height="currentPageHeight"
        :page-number="currentPage"
        :linked-chunk="linkedChunk"
        :saving="chunksStore.saving"
        :can-merge-text="Boolean(mergeCandidateRef)"
        :merging-text="mergingText"
        @save-chunk="onSaveChunk"
        @merge-preview-start="onMergePreviewStart"
        @merge-preview-end="onMergePreviewEnd"
        @merge-text="onMergeText"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Parse view (#264). Shows the Docling extraction graph for a document:
 *
 *   - LAYERS bar (chip filters per element type + Show labels toggle)
 *   - Structure tree (left rail — element hierarchy per page)
 *   - Page preview with bbox overlay (center)
 *
 * Two-way link between tree and overlay:
 *   - Selecting a node in the tree → highlight its bbox on the preview
 *   - Clicking a bbox → select the matching node in the tree
 */
import { computed, onMounted, ref, watch } from 'vue'
import type { DocChunk, DocTreeNode, PageElement } from '../shared/types'
import { useAnalysisStore } from '../features/analysis/store'
import { useChunksStore } from '../features/chunks/store'
import { useDocumentStore } from '../features/document/store'
import { chunkForElement } from '../features/document/linkedView'
import DocTreeRail from '../features/document/ui/DocTreeRail.vue'
import ElementProperties from '../features/document/ui/ElementProperties.vue'
import LayersBar from '../features/document/ui/LayersBar.vue'
import PagePreviewWithOverlay from '../features/document/ui/PagePreviewWithOverlay.vue'
import { useI18n } from '../shared/i18n'

const props = defineProps<{ docId: string }>()

const { t } = useI18n()
const documentStore = useDocumentStore()
const chunksStore = useChunksStore()
const analysisStore = useAnalysisStore()

async function onLaunchAnalysis(): Promise<void> {
  if (analysisStore.running) return
  await analysisStore.run(props.docId)
}

const currentPage = ref(1)
const hiddenTypes = ref<Set<string>>(new Set())

// Expand/Collapse all — bumping `treeRemountKey` re-keys the rail so every
// DocTreeNode mounts fresh and picks up the new `treeDefaultOpen` value.
const treeRemountKey = ref(0)
const treeDefaultOpen = ref<boolean | null>(null)
function onExpandAll(): void {
  treeDefaultOpen.value = true
  treeRemountKey.value++
}
function onCollapseAll(): void {
  treeDefaultOpen.value = false
  treeRemountKey.value++
}

const treeError = ref<string | null>(null)
const filter = ref('')
const selectedNodeRef = ref<string | null>(null)
const mergingText = ref(false)
const previewedMergeRef = ref<string | null>(null)

const currentPageData = computed(() => {
  return documentStore.workspacePages.find((p) => p.page_number === currentPage.value) ?? null
})

const currentPageElements = computed<PageElement[]>(() => currentPageData.value?.elements ?? [])
const currentPageWidth = computed(() => currentPageData.value?.width ?? 0)
const currentPageHeight = computed(() => currentPageData.value?.height ?? 0)

const selectedElement = computed<PageElement | null>(() => {
  return selectedElementBoxes.value[0]?.element ?? null
})

const selectedElementBoxes = computed<
  Array<{ pageNumber: number; pageWidth: number; pageHeight: number; element: PageElement }>
>(() => {
  if (!selectedNodeRef.value) return []
  const matches: Array<{ pageNumber: number; pageWidth: number; pageHeight: number; element: PageElement }> = []
  for (const page of documentStore.workspacePages) {
    for (const element of page.elements) {
      if (element.self_ref === selectedNodeRef.value) {
        matches.push({
          pageNumber: page.page_number,
          pageWidth: page.width,
          pageHeight: page.height,
          element,
        })
      }
    }
  }
  return matches
})

const linkedChunk = computed<DocChunk | null>(() => {
  if (!selectedElement.value) return null
  return chunkForElement(selectedElement.value, currentPage.value, chunksStore.chunks)
})

const mergeCandidateRef = computed<string | null>(() => {
  if (!selectedNodeRef.value || !selectedElement.value?.self_ref) return null
  return documentStore.getNextMergeableWorkspaceText(selectedNodeRef.value)
})

const nodeCount = computed(() => countNodes(tree.value))

const filteredNodes = computed<DocTreeNode[]>(() => {
  const needle = filter.value.trim().toLowerCase()
  if (!needle) return tree.value
  return filterTree(tree.value, needle)
})

const tree = computed<DocTreeNode[]>(() => {
  if (documentStore.workspaceTree.length > 0) {
    treeError.value = null
    return documentStore.workspaceTree
  }
  if (documentStore.workspaceLatestAnalysis?.documentJson) {
    treeError.value = 'Failed to derive document tree from documentJson'
  }
  return []
})

const highlightedRefs = computed<ReadonlySet<string>>(() => {
  const refs = new Set<string>()
  if (selectedNodeRef.value) refs.add(selectedNodeRef.value)
  if (previewedMergeRef.value) refs.add(previewedMergeRef.value)
  return refs
})

const bannerMessage = computed<string>(() => {
  const error = documentStore.workspaceError
  if (!error) {
    return t('parse.localDraftDirty')
  }
  return error.startsWith('parse.') ? t(error) : error
})

function reloadDerivedTree(): void {
  treeError.value = null
}

function onTreeSelect(ref: string): void {
  selectedNodeRef.value = ref
  const pageOfRef = findPageOfRef(documentStore.workspacePages, ref)
  if (pageOfRef !== null && pageOfRef !== currentPage.value) {
    currentPage.value = pageOfRef
  }
}

function onHoverElement(_el: PageElement | null): void {
  // Hover is informational only — selection drives the tree highlight.
}

function onClickElement(el: PageElement): void {
  if (el.self_ref) selectedNodeRef.value = el.self_ref
}

async function onSaveChunk(chunkId: string, text: string): Promise<void> {
  await chunksStore.updateText(props.docId, chunkId, text)
}

async function onMergeText(): Promise<void> {
  const leadingRef = selectedNodeRef.value
  const trailingRef = mergeCandidateRef.value
  if (!leadingRef || !trailingRef) return

  mergingText.value = true
  try {
    const { mergedText } = documentStore.mergeWorkspaceTexts(leadingRef, trailingRef)
    selectedNodeRef.value = leadingRef
    previewedMergeRef.value = null
  } catch (e) {
    treeError.value = (e as Error).message || 'Failed to merge text'
  } finally {
    mergingText.value = false
  }
}

function onMergePreviewStart(): void {
  previewedMergeRef.value = mergeCandidateRef.value
}

function onMergePreviewEnd(): void {
  previewedMergeRef.value = null
}

async function onDiscardLocalDraft(): Promise<void> {
  if (!documentStore.discardWorkspaceDraft()) return
  selectedNodeRef.value = null
  previewedMergeRef.value = null
}

onMounted(async () => {
  await Promise.all([
    documentStore.loadWorkspace(props.docId),
    chunksStore.load(props.docId),
  ])
  const first = documentStore.workspacePages[0]?.page_number
  if (first) currentPage.value = first
})

watch(
  () => props.docId,
  async (id) => {
    selectedNodeRef.value = null
    previewedMergeRef.value = null
    filter.value = ''
    await Promise.all([documentStore.loadWorkspace(id), chunksStore.load(id)])
    const first = documentStore.workspacePages[0]?.page_number
    if (first) currentPage.value = first
  },
)

watch(
  () => documentStore.workspaceActiveAnalysis?.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      selectedNodeRef.value = null
      previewedMergeRef.value = null
      treeError.value = null
    }
  },
)

// --- pure helpers ----------------------------------------------------------

function countNodes(nodes: readonly DocTreeNode[]): number {
  let n = 0
  for (const node of nodes) {
    n += 1 + countNodes(node.children)
  }
  return n
}

function filterTree(nodes: readonly DocTreeNode[], needle: string): DocTreeNode[] {
  const out: DocTreeNode[] = []
  for (const node of nodes) {
    const childMatches = filterTree(node.children, needle)
    const selfMatch =
      node.label.toLowerCase().includes(needle) || node.type.toLowerCase().includes(needle)
    if (selfMatch || childMatches.length > 0) {
      out.push({ ...node, children: childMatches })
    }
  }
  return out
}

function findPageOfRef(
  pages: readonly { page_number: number; elements: readonly { self_ref?: string }[] }[],
  ref: string,
): number | null {
  for (const page of pages) {
    if (page.elements.some((e) => e.self_ref === ref)) return page.page_number
  }
  return null
}

</script>

<style scoped>
.parse-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.parse-body {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  flex: 1;
  min-height: 0;
}

.parse-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--accent) 10%, var(--bg-surface));
}

.parse-banner-text {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.parse-banner-btn {
  margin-left: auto;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.parse-banner-btn:hover {
  border-color: var(--accent);
}

.parse-structure {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: var(--bg-surface);
  min-height: 0;
  overflow: hidden;
}

.parse-structure-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.parse-structure-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0;
  color: var(--text);
}

.parse-structure-count {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.parse-structure-actions {
  margin-left: auto;
  display: inline-flex;
  gap: 4px;
}

.tree-action-btn {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  line-height: 1;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.tree-action-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
}

.parse-structure-filter {
  margin: 8px 14px;
  padding: 6px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: 12px;
}

.parse-stage {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  overflow: hidden;
  min-height: 0;
}

.parse-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 13px;
}

.parse-state--empty {
  flex-direction: column;
  gap: 12px;
}

.tab-action-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: filter var(--transition);
}

.tab-action-cta:hover:not(:disabled) {
  filter: brightness(1.1);
}

.tab-action-cta:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.tab-action-spinner {
  width: 10px;
  height: 10px;
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
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
