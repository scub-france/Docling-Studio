<template>
  <div class="image-gallery">
    <div v-if="images.length === 0" class="gallery-empty">
      {{ t('results.noImages') }}
    </div>
    <div v-else class="gallery-grid">
      <div
        v-for="(img, idx) in images"
        :key="idx"
        class="gallery-card"
      >
        <div class="card-header">
          <span class="card-type">Picture</span>
          <span class="card-page">{{ t('results.page') }} {{ img.page }}</span>
        </div>
        <div class="card-content" v-if="img.content">
          {{ img.content.substring(0, 100) }}
        </div>
        <div class="card-bbox">
          <span class="bbox-label">bbox:</span>
          <span class="bbox-value">{{ img.bbox.map(v => Math.round(v)).join(', ') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../../../shared/i18n.js'

const { t } = useI18n()

const props = defineProps({
  pages: { type: Array, default: () => [] }
})

const images = computed(() => {
  const result = []
  for (const page of props.pages) {
    for (const el of page.elements) {
      if (el.type === 'picture') {
        result.push({ ...el, page: page.page_number })
      }
    }
  }
  return result
})
</script>

<style scoped>
.image-gallery {
  display: flex;
  flex-direction: column;
}

.gallery-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 40px;
  font-size: 14px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}

.gallery-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-type {
  font-size: 12px;
  font-weight: 600;
  color: #22C55E;
  text-transform: uppercase;
}

.card-page {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}

.card-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.card-bbox {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.bbox-label { margin-right: 4px; }
</style>
