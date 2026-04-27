<template>
  <div
    v-if="store.importDialogOpen"
    class="trace-modal-backdrop"
    data-e2e="reasoning-import-modal"
    @click.self="close"
  >
    <div
      class="trace-modal"
      role="dialog"
      aria-modal="true"
      :aria-label="t('reasoning.importTitle')"
    >
      <div class="trace-modal-header">
        <h3>{{ t('reasoning.importTitle') }}</h3>
        <button class="trace-modal-close" :aria-label="t('reasoning.close')" @click="close">
          ✕
        </button>
      </div>

      <p class="trace-modal-hint">{{ t('reasoning.importHint') }}</p>

      <div
        class="trace-drop"
        :class="{ dragging, parsing }"
        data-e2e="reasoning-drop-zone"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
        @click="openFilePicker"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".json,application/json"
          hidden
          @change="onFileSelect"
        />
        <div v-if="parsing" class="trace-drop-state">
          <div class="spinner" />
          <span>{{ t('reasoning.parsing') }}</span>
        </div>
        <div v-else class="trace-drop-state">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            class="trace-icon"
          >
            <path d="M12 16V4m0 0L8 8m4-4l4 4M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2" />
          </svg>
          <span class="trace-drop-title">{{ t('reasoning.drop') }}</span>
          <span class="trace-drop-sub">{{ t('reasoning.dropSub') }}</span>
        </div>
      </div>

      <details class="trace-paste">
        <summary>{{ t('reasoning.pasteToggle') }}</summary>
        <textarea
          v-model="pastedJson"
          class="trace-paste-area"
          :placeholder="t('reasoning.pastePlaceholder')"
          rows="6"
          data-e2e="reasoning-paste-area"
        />
        <button
          class="trace-paste-btn"
          :disabled="!pastedJson.trim() || parsing"
          @click="submitPasted"
        >
          {{ t('reasoning.pasteSubmit') }}
        </button>
      </details>

      <div v-if="errorMsg" class="trace-modal-error" data-e2e="reasoning-import-error">
        {{ errorMsg }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { useI18n } from '../../../shared/i18n'
import { useReasoningStore } from '../store'
import { parseImportedTrace } from '../store'

const store = useReasoningStore()
const { t } = useI18n()

const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const parsing = ref(false)
const pastedJson = ref('')
const errorMsg = ref<string | null>(null)

function close(): void {
  store.closeImportDialog()
  errorMsg.value = null
  pastedJson.value = ''
}

function openFilePicker(): void {
  fileInput.value?.click()
}

async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error ?? new Error('read failed'))
    reader.readAsText(file)
  })
}

function ingest(rawText: string): boolean {
  let raw: unknown
  try {
    raw = JSON.parse(rawText)
  } catch (e) {
    errorMsg.value = t('reasoning.errJson').replace('{msg}', (e as Error).message)
    return false
  }
  const parsed = parseImportedTrace(raw)
  if (!parsed) {
    errorMsg.value = t('reasoning.errShape')
    return false
  }
  errorMsg.value = null
  store.setResult(parsed.result, parsed.envelope)
  close()
  return true
}

async function handleFile(file: File): Promise<void> {
  errorMsg.value = null
  parsing.value = true
  try {
    const text = await readFileAsText(file)
    ingest(text)
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    parsing.value = false
  }
}

async function onFileSelect(e: Event): Promise<void> {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) await handleFile(file)
  target.value = ''
}

async function onDrop(e: DragEvent): Promise<void> {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await handleFile(file)
}

function submitPasted(): void {
  if (!pastedJson.value.trim()) return
  parsing.value = true
  try {
    ingest(pastedJson.value)
  } finally {
    parsing.value = false
  }
}
</script>

<style scoped>
.trace-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.trace-modal {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  width: min(560px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 12px 48px rgba(15, 23, 42, 0.25);
}

.trace-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.trace-modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.trace-modal-close {
  background: transparent;
  border: 0;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.trace-modal-close:hover {
  background: var(--border-light);
  color: var(--text);
}

.trace-modal-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 4px 0 16px;
}

.trace-drop {
  border: 2px dashed var(--border-light);
  border-radius: var(--radius);
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition);
}

.trace-drop:hover,
.trace-drop.dragging {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.trace-drop.parsing {
  pointer-events: none;
  opacity: 0.7;
}

.trace-drop-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.trace-icon {
  width: 32px;
  height: 32px;
  color: var(--text-muted);
}

.trace-drop-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.trace-drop-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.trace-paste {
  margin-top: 12px;
}

.trace-paste summary {
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 0;
}

.trace-paste-area {
  display: block;
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  resize: vertical;
}

.trace-paste-btn {
  margin-top: 8px;
  background: var(--accent);
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
}

.trace-paste-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.trace-modal-error {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: rgba(220, 38, 38, 0.08);
  color: var(--error, #dc2626);
  font-size: 12px;
}

.spinner {
  width: 24px;
  height: 24px;
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
