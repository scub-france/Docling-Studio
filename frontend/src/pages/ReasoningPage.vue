<template>
  <div v-if="phase === 'picker'" class="rp-host">
    <ReasoningDocPicker @select="onSelect" @uploaded="onUploaded" />
  </div>

  <div v-else-if="phase === 'preparing'" class="rp-host rp-centered" data-e2e="reasoning-preparing">
    <div class="rp-prep-card">
      <div class="spinner-large" />
      <div class="rp-prep-title">{{ prepTitle }}</div>
      <div v-if="prepHint" class="rp-prep-hint">{{ prepHint }}</div>
      <button class="rp-ghost" @click="goToPicker">{{ t('reasoning.cancel') }}</button>
    </div>
  </div>

  <div v-else-if="phase === 'error'" class="rp-host rp-centered" data-e2e="reasoning-error">
    <div class="rp-error-card">
      <div class="rp-error-title">{{ t('reasoning.prepError') }}</div>
      <p class="rp-error-msg">{{ errorMsg }}</p>
      <div class="rp-error-actions">
        <button class="rp-primary" @click="retry">{{ t('reasoning.retry') }}</button>
        <button class="rp-ghost" @click="goToPicker">{{ t('reasoning.pickAnother') }}</button>
      </div>
    </div>
  </div>

  <div v-else-if="phase === 'ready' && currentDocId" class="rp-host">
    <ReasoningWorkspace
      :doc-id="currentDocId"
      :doc-filename="currentDocFilename"
      @back="goToPicker"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAnalysisStore } from '../features/analysis/store'
import { useDocumentStore } from '../features/document/store'
import ReasoningDocPicker from '../features/reasoning/ui/ReasoningDocPicker.vue'
import ReasoningWorkspace from '../features/reasoning/ui/ReasoningWorkspace.vue'
import { useI18n } from '../shared/i18n'

const props = defineProps<{ docId?: string }>()

type Phase = 'picker' | 'preparing' | 'ready' | 'error'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const documentStore = useDocumentStore()
const analysisStore = useAnalysisStore()

const phase = ref<Phase>('picker')
const errorMsg = ref<string>('')
const prepTitle = ref<string>('')
const prepHint = ref<string | null>(null)

// When navigating via `/reasoning/:docId`, the router prop populates here.
// `route.params.docId` is the reactive source of truth.
const currentDocId = computed<string | null>(() => {
  const raw = props.docId ?? (route.params.docId as string | undefined)
  return raw || null
})

const currentDocFilename = computed<string | null>(() => {
  if (!currentDocId.value) return null
  const doc = documentStore.documents.find((d) => d.id === currentDocId.value)
  return doc?.filename ?? null
})

/**
 * Drive the doc through the prepare pipeline: ensure a completed analysis
 * exists (run one silently if not). The graph itself is built on demand from
 * SQLite by `/api/documents/:id/reasoning-graph`, so no priming step is needed.
 */
async function prepareDoc(docId: string): Promise<void> {
  phase.value = 'preparing'
  errorMsg.value = ''

  try {
    if (documentStore.documents.length === 0) await documentStore.load()
    if (analysisStore.analyses.length === 0) await analysisStore.load()

    const completed = analysisStore.analyses.find(
      (a) => a.documentId === docId && a.status === 'COMPLETED' && a.hasDocumentJson,
    )

    if (!completed) {
      // Silent analysis with defaults — the tunnel doesn't expose pipeline
      // options (see design §(b) silencieux).
      prepTitle.value = t('reasoning.analyzing')
      prepHint.value = t('reasoning.analyzingHint')
      await analysisStore.run(docId)
      await waitForAnalysisIdle()
      const again = analysisStore.analyses.find(
        (a) => a.documentId === docId && a.status === 'COMPLETED' && a.hasDocumentJson,
      )
      if (!again) {
        throw new Error(analysisStore.error || t('reasoning.prepErrAnalysis'))
      }
    }

    phase.value = 'ready'
  } catch (e) {
    errorMsg.value = (e as Error).message || t('reasoning.prepErrUnknown')
    phase.value = 'error'
  }
}

function waitForAnalysisIdle(timeoutMs = 10 * 60 * 1000): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!analysisStore.running) return resolve()
    const started = Date.now()
    const id = window.setInterval(() => {
      if (!analysisStore.running) {
        window.clearInterval(id)
        resolve()
      } else if (Date.now() - started > timeoutMs) {
        window.clearInterval(id)
        reject(new Error(t('reasoning.prepErrTimeout')))
      }
    }, 500)
  })
}

function onSelect(docId: string): void {
  router.push({ name: 'reasoning-doc', params: { docId } })
}

function onUploaded(docId: string): void {
  router.push({ name: 'reasoning-doc', params: { docId } })
}

function goToPicker(): void {
  router.push({ name: 'reasoning' })
}

async function retry(): Promise<void> {
  if (currentDocId.value) await prepareDoc(currentDocId.value)
}

// React to route param changes (pushes, back/forward).
watch(
  currentDocId,
  (id) => {
    if (!id) {
      phase.value = 'picker'
      return
    }
    void prepareDoc(id)
  },
  { immediate: false },
)

onMounted(() => {
  if (currentDocId.value) void prepareDoc(currentDocId.value)
  else phase.value = 'picker'
})
</script>

<style scoped>
.rp-host {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.rp-centered {
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

.rp-prep-card,
.rp-error-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  padding: 32px 40px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-align: center;
  max-width: 480px;
}

.rp-prep-title,
.rp-error-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.rp-prep-hint,
.rp-error-msg {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}

.rp-error-msg {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  padding: 8px 12px;
  background: rgba(220, 38, 38, 0.08);
  color: var(--error, #dc2626);
  border-radius: var(--radius-sm);
  width: 100%;
  text-align: left;
}

.rp-error-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.rp-primary {
  background: var(--accent);
  color: white;
  border: 0;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.rp-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 14px;
  font-size: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.spinner-large {
  width: 36px;
  height: 36px;
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
