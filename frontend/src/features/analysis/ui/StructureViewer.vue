<template>
  <div class="structure-viewer">
    <!-- Page selector -->
    <div class="page-selector" v-if="pages.length > 1">
      <button
        v-for="p in pages"
        :key="p.page_number"
        class="page-btn"
        :class="{ active: selectedPage === p.page_number }"
        @click="selectedPage = p.page_number"
      >
        {{ p.page_number }}
      </button>
    </div>

    <!-- Legend -->
    <div class="legend">
      <button
        v-for="[type, color] in Object.entries(ELEMENT_COLORS)"
        :key="type"
        class="legend-item"
        :class="{ dimmed: hiddenTypes.has(type) }"
        @click="toggleType(type)"
      >
        <span class="legend-dot" :style="{ background: color }" />
        <span>{{ type }}</span>
        <span class="legend-count">{{ countElements(type) }}</span>
      </button>
    </div>

    <!-- Canvas overlay -->
    <div class="canvas-container" ref="containerRef">
      <img
        v-if="documentId"
        :src="previewUrl ?? undefined"
        class="page-image"
        ref="imageRef"
        @load="onImageLoad"
      />
      <canvas
        ref="canvasRef"
        class="overlay-canvas"
        @mousemove="onMouseMove"
        @mouseleave="hoveredElement = null"
      />
      <!-- Tooltip -->
      <div
        v-if="hoveredElement"
        class="tooltip"
        :style="tooltipStyle"
      >
        <span class="tooltip-type" :style="{ color: ELEMENT_COLORS[hoveredElement.type] || ELEMENT_COLORS.text }">
          {{ hoveredElement.type }}
        </span>
        <span class="tooltip-content">{{ hoveredElement.content?.substring(0, 150) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, reactive } from 'vue'
import { getPreviewUrl } from '../../document/api'
import { computeScale, bboxToRect, pointInRect } from '../bboxScaling'
import type { Page, PageElement } from '../../../shared/types'

const ELEMENT_COLORS: Record<string, string> = {
  section_header: '#F97316',
  text: '#3B82F6',
  table: '#8B5CF6',
  picture: '#22C55E',
  list: '#06B6D4',
  formula: '#EC4899',
  caption: '#EAB308'
}

const props = defineProps({
  pages: { type: Array as () => Page[], default: () => [] },
  documentId: String
})

const selectedPage = ref(1)
const hiddenTypes = reactive(new Set<string>())
const containerRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const hoveredElement = ref<PageElement | null>(null)
const tooltipStyle = ref<Record<string, string>>({})
const imageSize = ref({ width: 0, height: 0 })

const currentPageData = computed(() => {
  return props.pages.find(p => p.page_number === selectedPage.value)
})

const visibleElements = computed(() => {
  if (!currentPageData.value) return []
  return currentPageData.value.elements.filter(e => !hiddenTypes.has(e.type))
})

const previewUrl = computed(() => {
  if (!props.documentId) return null
  return getPreviewUrl(props.documentId, selectedPage.value)
})

function toggleType(type: string) {
  if (hiddenTypes.has(type)) hiddenTypes.delete(type)
  else hiddenTypes.add(type)
  drawOverlay()
}

function countElements(type: string) {
  if (!currentPageData.value) return 0
  return currentPageData.value.elements.filter(e => e.type === type).length
}

function onImageLoad() {
  const img = imageRef.value
  if (!img) return
  imageSize.value = { width: img.naturalWidth, height: img.naturalHeight }
  nextTick(drawOverlay)
}

function drawOverlay() {
  const canvas = canvasRef.value
  const img = imageRef.value
  if (!canvas || !img) return

  canvas.width = img.clientWidth
  canvas.height = img.clientHeight

  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const page = currentPageData.value
  if (!page) return

  const scale = computeScale(img.clientWidth, img.clientHeight, page.width, page.height)

  for (const el of visibleElements.value) {
    const rect = bboxToRect(el.bbox, scale)
    const color = ELEMENT_COLORS[el.type] || ELEMENT_COLORS.text

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.strokeRect(rect.x, rect.y, rect.w, rect.h)

    ctx.fillStyle = color + '20'
    ctx.fillRect(rect.x, rect.y, rect.w, rect.h)
  }
}

function onMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  const page = currentPageData.value
  const img = imageRef.value
  if (!canvas || !page || !img) return

  const canvasRect = canvas.getBoundingClientRect()
  const mx = e.clientX - canvasRect.left
  const my = e.clientY - canvasRect.top

  const scale = computeScale(img.clientWidth, img.clientHeight, page.width, page.height)

  let found: PageElement | null = null
  for (const el of visibleElements.value) {
    if (pointInRect(mx, my, bboxToRect(el.bbox, scale))) {
      found = el
      break
    }
  }

  hoveredElement.value = found
  if (found) {
    tooltipStyle.value = {
      left: `${Math.min(mx + 12, canvas.width - 250)}px`,
      top: `${my + 12}px`
    }
  }
}

watch([() => props.pages, selectedPage, hiddenTypes], () => {
  nextTick(drawOverlay)
})
</script>

<style scoped>
.structure-viewer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-selector {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  font-family: 'IBM Plex Mono', monospace;
  cursor: pointer;
  transition: all var(--transition);
}

.page-btn:hover { background: var(--bg-hover); }
.page-btn.active {
  background: var(--accent-muted);
  border-color: var(--accent);
  color: var(--accent);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 16px;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.legend-item:hover { background: var(--bg-hover); }
.legend-item.dimmed { opacity: 0.4; }

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-count {
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.canvas-container {
  position: relative;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.page-image {
  width: 100%;
  display: block;
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: auto;
}

.tooltip {
  position: absolute;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  max-width: 250px;
  pointer-events: none;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.tooltip-type {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.tooltip-content {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  word-break: break-word;
}
</style>
