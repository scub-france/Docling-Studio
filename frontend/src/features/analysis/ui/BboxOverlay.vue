<template>
  <div class="bbox-overlay">
    <!-- Legend bar -->
    <div class="overlay-legend" v-if="pageData">
      <button
        v-for="[type, color] in Object.entries(ELEMENT_COLORS)"
        :key="type"
        class="legend-chip"
        :class="{ dimmed: hiddenTypes.has(type) }"
        @click="toggleType(type)"
      >
        <span class="legend-dot" :style="{ background: color }" />
        <span>{{ type }}</span>
        <span class="legend-count">{{ countElements(type) }}</span>
      </button>
    </div>

    <!-- Canvas + Tooltip (positioned over image via parent) -->
    <canvas
      ref="canvasRef"
      class="overlay-canvas"
      @mousemove="onMouseMove"
      @mouseleave="hoveredElement = null"
    />
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
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive, onMounted, onBeforeUnmount } from 'vue'
import { computeScale, bboxToRect, pointInRect } from '../bboxScaling.js'

const ELEMENT_COLORS = {
  section_header: '#F97316',
  text: '#3B82F6',
  table: '#8B5CF6',
  picture: '#22C55E',
  list: '#06B6D4',
  formula: '#EC4899',
  caption: '#EAB308'
}

const props = defineProps({
  /** The <img> element to overlay onto */
  imageEl: { type: Object, default: null },
  /** Page data { page_number, width, height, elements[] } for current page */
  pageData: { type: Object, default: null }
})

const hiddenTypes = reactive(new Set())
const canvasRef = ref(null)
const hoveredElement = ref(null)
const tooltipStyle = ref({})

const visibleElements = computed(() => {
  if (!props.pageData) return []
  return props.pageData.elements.filter(e => !hiddenTypes.has(e.type))
})

function toggleType(type) {
  if (hiddenTypes.has(type)) hiddenTypes.delete(type)
  else hiddenTypes.add(type)
  draw()
}

function countElements(type) {
  if (!props.pageData) return 0
  return props.pageData.elements.filter(e => e.type === type).length
}

function draw() {
  const canvas = canvasRef.value
  const img = props.imageEl
  if (!canvas || !img) return

  // Wait until image is loaded (clientWidth > 0)
  if (!img.clientWidth || !img.clientHeight) return

  canvas.width = img.clientWidth
  canvas.height = img.clientHeight

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  if (!props.pageData) return

  const scale = computeScale(img.clientWidth, img.clientHeight, props.pageData.width, props.pageData.height)

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

function onMouseMove(e) {
  const canvas = canvasRef.value
  const img = props.imageEl
  if (!canvas || !img || !props.pageData) return

  const canvasRect = canvas.getBoundingClientRect()
  const mx = e.clientX - canvasRect.left
  const my = e.clientY - canvasRect.top

  const scale = computeScale(img.clientWidth, img.clientHeight, props.pageData.width, props.pageData.height)

  let found = null
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

// Redraw on resize
let resizeObserver = null
onMounted(() => {
  if (props.imageEl) {
    resizeObserver = new ResizeObserver(() => draw())
    resizeObserver.observe(props.imageEl)
  }
})
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

// Redraw when data or image changes
watch([() => props.pageData, () => props.imageEl, hiddenTypes], () => {
  nextTick(draw)
})

// Expose draw so parent can call it after image load
defineExpose({ draw })
</script>

<style scoped>
.bbox-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.overlay-legend {
  position: absolute;
  top: 8px;
  left: 8px;
  right: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  z-index: 5;
  pointer-events: auto;
}

.legend-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
  backdrop-filter: blur(8px);
  opacity: 0.9;
}

.legend-chip:hover { opacity: 1; background: var(--bg-hover); }
.legend-chip.dimmed { opacity: 0.35; }

.legend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-count {
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: auto;
  /* No CSS width/height — dimensions set purely by canvas.width/height in JS
     to avoid browser stretching the canvas content */
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
