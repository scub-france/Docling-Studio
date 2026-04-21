<template>
  <div
    v-if="store.runDialogOpen"
    class="run-modal-backdrop"
    data-e2e="reasoning-run-modal"
    @click.self="close"
  >
    <div class="run-modal" role="dialog" aria-modal="true" :aria-label="t('reasoning.runTitle')">
      <div class="run-modal-header">
        <h3>{{ t('reasoning.runTitle') }}</h3>
        <button
          class="run-modal-close"
          :aria-label="t('reasoning.close')"
          :disabled="store.running"
          @click="close"
        >
          ✕
        </button>
      </div>

      <p class="run-modal-hint">{{ t('reasoning.runHint') }}</p>

      <label class="run-field">
        <span class="run-field-label">{{ t('reasoning.runQueryLabel') }}</span>
        <textarea
          v-model="query"
          class="run-field-input"
          rows="3"
          :placeholder="t('reasoning.runQueryPlaceholder')"
          :disabled="store.running"
          data-e2e="reasoning-run-query"
        />
      </label>

      <label class="run-field">
        <span class="run-field-label">{{ t('reasoning.runModelLabel') }}</span>
        <input
          v-model="modelId"
          type="text"
          class="run-field-input"
          :placeholder="t('reasoning.runModelPlaceholder')"
          :disabled="store.running"
          data-e2e="reasoning-run-model"
        />
        <span class="run-field-sub">{{ t('reasoning.runModelSub') }}</span>
      </label>

      <div v-if="store.running" class="run-loading" data-e2e="reasoning-run-loading">
        <div class="spinner" />
        <span>{{ t('reasoning.running') }}</span>
      </div>

      <div v-if="errorMsg" class="run-modal-error" data-e2e="reasoning-run-error">
        {{ errorMsg }}
      </div>

      <div class="run-modal-actions">
        <button class="run-ghost" :disabled="store.running" @click="close">
          {{ t('reasoning.cancel') }}
        </button>
        <button
          class="run-primary"
          :disabled="!query.trim() || store.running"
          data-e2e="reasoning-run-submit"
          @click="submit"
        >
          {{ t('reasoning.runSubmit') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { useI18n } from '../../../shared/i18n'
import { runReasoning } from '../api'
import { useReasoningStore } from '../store'
import type { SidecarEnvelope } from '../types'

const props = defineProps<{ docId: string; docFilename?: string | null }>()

const store = useReasoningStore()
const { t } = useI18n()

const query = ref('')
const modelId = ref('')
const errorMsg = ref<string | null>(null)

function close(): void {
  if (store.running) return // don't let the user close mid-run
  store.closeRunDialog()
  errorMsg.value = null
}

async function submit(): Promise<void> {
  const q = query.value.trim()
  if (!q) return
  errorMsg.value = null
  store.setRunning(true)
  try {
    const result = await runReasoning(props.docId, q, modelId.value.trim() || undefined)
    // Synthesize a sidecar-like envelope so the panel can show what was asked
    // and which model answered, same as an imported trace.
    const envelope: SidecarEnvelope = {
      filename: props.docFilename ?? undefined,
      query: q,
      model: modelId.value.trim()
        ? { ollama_name: modelId.value.trim(), hf_model_name: null }
        : undefined,
      result,
    }
    store.setResult(result, envelope)
    // Keep the query for the user's reference but close the dialog.
    store.closeRunDialog()
  } catch (e) {
    errorMsg.value = (e as Error).message || t('reasoning.runErrUnknown')
  } finally {
    store.setRunning(false)
  }
}
</script>

<style scoped>
.run-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.run-modal {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  width: min(560px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 12px 48px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.run-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.run-modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.run-modal-close {
  background: transparent;
  border: 0;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.run-modal-close:hover:not(:disabled) {
  background: var(--border-light);
  color: var(--text);
}

.run-modal-close:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.run-modal-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

.run-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.run-field-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.run-field-input {
  width: 100%;
  padding: 8px;
  font-size: 13px;
  font-family: inherit;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  resize: vertical;
}

.run-field-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.run-field-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.run-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 12px;
  background: var(--accent-muted, rgba(234, 88, 12, 0.08));
  border-radius: var(--radius-sm);
}

.run-modal-error {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: rgba(220, 38, 38, 0.08);
  color: var(--error, #dc2626);
  font-size: 12px;
  font-family: 'IBM Plex Mono', monospace;
  word-break: break-word;
}

.run-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.run-primary {
  background: var(--accent);
  color: white;
  border: 0;
  padding: 7px 16px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.run-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.run-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 7px 14px;
  font-size: 13px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.run-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 18px;
  height: 18px;
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
