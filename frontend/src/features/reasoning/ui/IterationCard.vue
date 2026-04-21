<template>
  <button
    type="button"
    class="it-card"
    :class="{ active, missing: !iteration.present, converged: iteration.canAnswer }"
    :data-e2e="`reasoning-iteration-${iteration.iteration}`"
    @click="$emit('focus', iteration.iteration)"
  >
    <div class="it-row">
      <span class="it-badge">{{ iteration.iteration }}</span>
      <span class="it-ref" :title="iteration.sectionRef">{{ iteration.sectionRef }}</span>
      <span
        class="it-status"
        :class="{
          ok: iteration.canAnswer,
          more: !iteration.canAnswer && iteration.present,
          missing: !iteration.present,
        }"
      >
        {{ statusLabel }}
      </span>
    </div>
    <p v-if="iteration.reason" class="it-reason">{{ iteration.reason }}</p>
    <p v-if="iteration.response && iteration.canAnswer" class="it-response">
      {{ iteration.response }}
    </p>
    <div class="it-meta">
      <span v-if="iteration.sectionTextLength">
        {{ t('reasoning.charsLabel').replace('{n}', String(iteration.sectionTextLength)) }}
      </span>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useI18n } from '../../../shared/i18n'
import type { ResolvedIteration } from '../types'

const props = defineProps<{
  iteration: ResolvedIteration
  active: boolean
}>()

defineEmits<{ focus: [iteration: number] }>()

const { t } = useI18n()

const statusLabel = computed(() => {
  if (!props.iteration.present) return t('reasoning.statusMissing')
  if (props.iteration.canAnswer) return t('reasoning.statusAnswered')
  return t('reasoning.statusMore')
})
</script>

<style scoped>
.it-card {
  display: block;
  width: 100%;
  text-align: left;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  cursor: pointer;
  transition: all var(--transition);
  font-family: inherit;
  color: inherit;
}

.it-card:hover {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.it-card.active {
  border-color: #ea580c;
  box-shadow: 0 0 0 2px rgba(234, 88, 12, 0.2);
  background: rgba(234, 88, 12, 0.06);
}

.it-card.missing {
  opacity: 0.6;
}

.it-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.it-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ea580c;
  color: #ffffff;
  font-weight: 700;
  font-size: 11px;
}

.it-card.missing .it-badge {
  background: var(--text-muted);
}

.it-ref {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1 1 auto;
}

.it-status {
  flex: 0 0 auto;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.it-status.ok {
  background: rgba(22, 163, 74, 0.15);
  color: #15803d;
}

.it-status.more {
  background: rgba(234, 179, 8, 0.15);
  color: #a16207;
}

.it-status.missing {
  background: var(--border-light);
  color: var(--text-muted);
}

.it-reason {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text);
}

.it-response {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-secondary);
  font-style: italic;
  padding: 6px 8px;
  border-left: 2px solid #ea580c;
  background: rgba(234, 88, 12, 0.04);
  border-radius: 2px;
}

.it-meta {
  margin-top: 6px;
  font-size: 10px;
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
}
</style>
