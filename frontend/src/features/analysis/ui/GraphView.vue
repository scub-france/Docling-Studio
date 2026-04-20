<template>
  <div class="graph-view" data-e2e="graph-view">
    <div v-if="loading" class="graph-placeholder">
      <div class="spinner-large" />
      <span>{{ t('results.graphLoading') }}</span>
    </div>
    <div v-else-if="error" class="graph-placeholder error" data-e2e="graph-error">
      <span>{{ error }}</span>
      <button class="retry-btn" @click="load">{{ t('results.retry') }}</button>
    </div>
    <div v-else-if="empty" class="graph-placeholder">
      <span>{{ t('results.graphEmpty') }}</span>
    </div>
    <template v-else>
      <div class="graph-toolbar">
        <span class="graph-stats">
          {{ payload?.node_count }} nodes · {{ payload?.edge_count }} edges ·
          {{ payload?.page_count }} pages
        </span>
        <span class="graph-legend">
          <span class="legend-chip legend-document">Document</span>
          <span class="legend-chip legend-section">Section</span>
          <span class="legend-chip legend-paragraph">Paragraph</span>
          <span class="legend-chip legend-table">Table</span>
          <span class="legend-chip legend-figure">Figure</span>
          <span class="legend-chip legend-page">Page</span>
          <span class="legend-chip legend-chunk">Chunk</span>
        </span>
      </div>
      <div ref="containerRef" class="graph-canvas" data-e2e="graph-canvas" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useI18n } from '../../../shared/i18n'
import { fetchDocumentGraph, type GraphPayload } from '../graphApi'

const props = defineProps<{ docId: string | null }>()
const { t } = useI18n()

const containerRef = ref<HTMLDivElement | null>(null)
const payload = ref<GraphPayload | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const empty = ref(false)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let cy: any | null = null

const NODE_COLORS: Record<string, string> = {
  document: '#1E293B',
  SectionHeader: '#F97316',
  Paragraph: '#3B82F6',
  TextElement: '#3B82F6',
  Table: '#8B5CF6',
  Figure: '#22C55E',
  ListItem: '#06B6D4',
  Formula: '#EC4899',
  Code: '#14B8A6',
  Caption: '#EAB308',
  Page: '#94A3B8',
  Chunk: '#DC2626',
}

function nodeColor(n: GraphPayload['nodes'][number]): string {
  if (n.group === 'document') return NODE_COLORS.document
  if (n.group === 'page') return NODE_COLORS.Page
  if (n.group === 'chunk') return NODE_COLORS.Chunk
  return NODE_COLORS[n.label || 'TextElement'] || NODE_COLORS.TextElement
}

function nodeLabel(n: GraphPayload['nodes'][number]): string {
  if (n.group === 'document') return n.title || n.id
  if (n.group === 'page') return `p.${n.page_no}`
  if (n.group === 'chunk') return `chunk #${n.chunk_index}`
  const txt = (n.text || '').slice(0, 40)
  return txt || n.label || n.docling_label || n.self_ref || n.id
}

async function load(): Promise<void> {
  if (!props.docId) {
    empty.value = true
    return
  }
  loading.value = true
  error.value = null
  empty.value = false
  try {
    payload.value = await fetchDocumentGraph(props.docId)
    if (!payload.value.nodes.length) {
      empty.value = true
      return
    }
    // Flip loading off so the canvas <div> mounts, then wait a tick before init.
    loading.value = false
    await nextTick()
    await renderGraph()
  } catch (e) {
    error.value = (e as Error).message || 'Failed to load graph'
    console.error('Failed to load graph', e)
  } finally {
    loading.value = false
  }
}

async function renderGraph(): Promise<void> {
  if (!containerRef.value || !payload.value) return
  // Dynamic import keeps cytoscape out of the main chunk.
  const [{ default: cytoscape }, { default: dagre }] = await Promise.all([
    import('cytoscape'),
    import('cytoscape-dagre'),
  ])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(cytoscape as any).use(dagre)

  if (cy) {
    cy.destroy()
    cy = null
  }

  const elements = [
    ...payload.value.nodes.map((n) => ({
      data: {
        id: n.id,
        label: nodeLabel(n),
        bg: nodeColor(n),
        group: n.group,
        raw: n,
      },
    })),
    ...payload.value.edges.map((e) => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
      },
    })),
  ]

  cy = cytoscape({
    container: containerRef.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': 'data(bg)',
          label: 'data(label)',
          color: '#0F172A',
          'font-size': 10,
          'text-wrap': 'ellipsis',
          'text-max-width': '140px',
          'text-valign': 'center',
          'text-halign': 'center',
          width: 28,
          height: 28,
          'border-width': 1,
          'border-color': '#0F172A',
        },
      },
      {
        selector: 'node[group = "document"]',
        style: { shape: 'round-rectangle', width: 60, height: 36, color: '#F8FAFC' },
      },
      {
        selector: 'node[group = "page"]',
        style: { shape: 'round-rectangle', width: 40, height: 24 },
      },
      {
        selector: 'node[group = "chunk"]',
        style: { shape: 'diamond', color: '#F8FAFC' },
      },
      {
        selector: 'edge',
        style: {
          width: 1,
          'line-color': '#94A3B8',
          'target-arrow-color': '#94A3B8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'font-size': 8,
          color: '#64748B',
        },
      },
      {
        selector: 'edge[type = "PARENT_OF"]',
        style: { 'line-color': '#1E293B', 'target-arrow-color': '#1E293B', width: 1.5 },
      },
      {
        selector: 'edge[type = "NEXT"]',
        style: { 'line-style': 'dashed', 'line-color': '#64748B' },
      },
      {
        selector: 'edge[type = "ON_PAGE"]',
        style: { 'line-color': '#CBD5E1', width: 1 },
      },
      {
        selector: 'edge[type = "DERIVED_FROM"]',
        style: { 'line-color': '#DC2626', 'target-arrow-color': '#DC2626' },
      },
    ],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    layout: {
      name: 'dagre',
      rankDir: 'TB',
      nodeSep: 30,
      edgeSep: 10,
      rankSep: 40,
    } as any,
    wheelSensitivity: 0.15,
  })
}

function disposeGraph(): void {
  if (cy) {
    cy.destroy()
    cy = null
  }
}

onMounted(load)
onBeforeUnmount(disposeGraph)
watch(
  () => props.docId,
  () => {
    disposeGraph()
    load()
  },
)
</script>

<style scoped>
.graph-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.graph-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
  flex-wrap: wrap;
}

.graph-stats {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.graph-legend {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.legend-chip {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  color: #f8fafc;
}

.legend-document {
  background: #1e293b;
}
.legend-section {
  background: #f97316;
}
.legend-paragraph {
  background: #3b82f6;
}
.legend-table {
  background: #8b5cf6;
}
.legend-figure {
  background: #22c55e;
}
.legend-page {
  background: #94a3b8;
  color: #0f172a;
}
.legend-chunk {
  background: #dc2626;
}

.graph-canvas {
  flex: 1;
  min-height: 0;
  background: var(--bg);
}

.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-muted);
  font-size: 14px;
  padding: 32px;
  text-align: center;
}

.graph-placeholder.error {
  color: var(--error);
}

.retry-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
}

.spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
