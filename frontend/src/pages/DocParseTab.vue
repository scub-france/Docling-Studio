<template>
  <div class="parse-tab" data-e2e="parse-tab">
    <LayersBar
      :elements="currentPageElements"
      :hidden-types="hiddenTypes"
      :show-labels="showLabels"
      @update:hidden-types="(next) => (hiddenTypes = next)"
      @update:show-labels="(next) => (showLabels = next)"
    />
    <div class="parse-body">
      <aside class="parse-structure">
        <header class="parse-structure-header">
          <h2 class="parse-structure-title">{{ t('parse.structureTitle') }}</h2>
          <span class="parse-structure-count">
            {{ t('parse.structureNodes', { n: nodeCount }) }}
          </span>
        </header>
        <input
          v-model="filter"
          type="text"
          class="parse-structure-filter"
          :placeholder="t('parse.filterPlaceholder')"
          data-e2e="structure-filter"
        />
        <DocTreeRail
          :nodes="filteredNodes"
          :loading="treeLoading"
          :error="treeError"
          :selected="selectedNodeRef"
          :highlight="selectedNodeRef"
          @select="onTreeSelect"
          @reload="loadTree"
        />
      </aside>
      <div class="parse-stage">
        <PagePreviewWithOverlay
          v-if="documentStore.workspacePages.length"
          :document-id="docId"
          :pages="documentStore.workspacePages"
          :current-page="currentPage"
          :hidden-types="hiddenTypes"
          :show-labels="showLabels"
          :highlighted-refs="highlightedRefs"
          @update:current-page="(p) => (currentPage = p)"
          @hover-element="onHoverElement"
          @click-element="onClickElement"
        />
        <div v-else-if="documentStore.workspaceLoading" class="parse-state">
          <span class="spinner" />
        </div>
        <div v-else class="parse-state">
          {{ t('parse.noAnalysis') }}
        </div>
      </div>
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
import type { DocTreeNode, PageElement } from '../shared/types'
import { fetchDocumentTree } from '../features/document/api'
import { useDocumentStore } from '../features/document/store'
import DocTreeRail from '../features/document/ui/DocTreeRail.vue'
import LayersBar from '../features/document/ui/LayersBar.vue'
import PagePreviewWithOverlay from '../features/document/ui/PagePreviewWithOverlay.vue'
import { useI18n } from '../shared/i18n'

const props = defineProps<{ docId: string }>()

const { t } = useI18n()
const documentStore = useDocumentStore()

const currentPage = ref(1)
const hiddenTypes = ref<Set<string>>(new Set())
const showLabels = ref(false)

const tree = ref<DocTreeNode[]>([])
const treeLoading = ref(false)
const treeError = ref<string | null>(null)
const filter = ref('')
const selectedNodeRef = ref<string | null>(null)

const currentPageElements = computed<PageElement[]>(() => {
  const page = documentStore.workspacePages.find((p) => p.page_number === currentPage.value)
  return page?.elements ?? []
})

const nodeCount = computed(() => countNodes(tree.value))

const filteredNodes = computed<DocTreeNode[]>(() => {
  const needle = filter.value.trim().toLowerCase()
  if (!needle) return tree.value
  return filterTree(tree.value, needle)
})

const highlightedRefs = computed<ReadonlySet<string>>(() => {
  if (!selectedNodeRef.value) return new Set()
  return new Set([selectedNodeRef.value])
})

async function loadTree(): Promise<void> {
  treeLoading.value = true
  treeError.value = null
  try {
    tree.value = await fetchDocumentTree(props.docId)
  } catch (e) {
    treeError.value = (e as Error).message || 'Failed to load tree'
  } finally {
    treeLoading.value = false
  }
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

onMounted(async () => {
  await Promise.all([documentStore.loadWorkspace(props.docId), loadTree()])
  const first = documentStore.workspacePages[0]?.page_number
  if (first) currentPage.value = first
})

watch(
  () => props.docId,
  async (id) => {
    selectedNodeRef.value = null
    filter.value = ''
    await Promise.all([documentStore.loadWorkspace(id), loadTree()])
    const first = documentStore.workspacePages[0]?.page_number
    if (first) currentPage.value = first
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
  grid-template-columns: 320px minmax(0, 1fr);
  flex: 1;
  min-height: 0;
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
