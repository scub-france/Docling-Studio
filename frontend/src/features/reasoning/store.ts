import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type { OverlayResult, ReasoningResult, ResolvedIteration, SidecarEnvelope } from './types'

/**
 * Parse an arbitrary JSON payload as either:
 *   - a bare `ReasoningResult` (what `docling-agent` emits directly), or
 *   - the sidecar envelope (`{ job_id, filename, query, model, result }`)
 *
 * Returns `null` if the shape doesn't match either.
 */
export function parseImportedTrace(
  raw: unknown,
): { result: ReasoningResult; envelope: SidecarEnvelope | null } | null {
  if (!raw || typeof raw !== 'object') return null
  const obj = raw as Record<string, unknown>

  // Envelope shape
  if (obj.result && typeof obj.result === 'object') {
    const result = obj.result as ReasoningResult
    if (isReasoningResult(result)) {
      return { result, envelope: obj as unknown as SidecarEnvelope }
    }
  }
  // Bare ReasoningResult
  if (isReasoningResult(obj as unknown as ReasoningResult)) {
    return { result: obj as unknown as ReasoningResult, envelope: null }
  }
  return null
}

function isReasoningResult(x: ReasoningResult | undefined): boolean {
  if (!x || typeof x !== 'object') return false
  return (
    typeof x.answer === 'string' && typeof x.converged === 'boolean' && Array.isArray(x.iterations)
  )
}

export const useReasoningStore = defineStore('reasoning', () => {
  const importDialogOpen = ref(false)
  // Separate modal for the live runner (POST /api/documents/:id/reasoning),
  // so it can coexist with the import dialog conceptually even if only one
  // is ever open at a time.
  const runDialogOpen = ref(false)
  const running = ref(false)
  const rawResult = ref<ReasoningResult | null>(null)
  const envelope = ref<SidecarEnvelope | null>(null)
  const overlay = ref<OverlayResult | null>(null)
  const activeIteration = ref<number | null>(null)
  const error = ref<string | null>(null)
  // Focus mode: when true, non-visited elements are dimmed so the trace pops.
  // Default ON because that's the primary value of the feature; user can
  // switch it off from the panel to see the trace in the full graph context.
  const focusMode = ref(true)

  const hasTrace = computed(() => rawResult.value !== null)
  const iterations = computed<ResolvedIteration[]>(() => overlay.value?.resolved ?? [])
  const presentCount = computed(() => overlay.value?.presentCount ?? 0)
  const missingCount = computed(() => overlay.value?.missingCount ?? 0)

  function openImportDialog(): void {
    importDialogOpen.value = true
  }

  function closeImportDialog(): void {
    importDialogOpen.value = false
  }

  function openRunDialog(): void {
    runDialogOpen.value = true
  }

  function closeRunDialog(): void {
    runDialogOpen.value = false
  }

  function setRunning(v: boolean): void {
    running.value = v
  }

  /**
   * Called by `ImportTraceDialog` once the user has supplied a JSON file.
   * Does NOT touch Cytoscape — the `ReasoningPanel` watches `rawResult` and
   * reapplies the overlay via `graphReasoningOverlay.applyReasoningOverlay`.
   */
  function setResult(result: ReasoningResult, env: SidecarEnvelope | null): void {
    rawResult.value = result
    envelope.value = env
    error.value = null
    activeIteration.value = null
  }

  function setOverlay(o: OverlayResult | null): void {
    overlay.value = o
  }

  function setActiveIteration(n: number | null): void {
    // Pure state — drives the active-card highlight in the iteration list.
    // Side effects (graph pan, PDF scroll) are dispatched imperatively from
    // ReasoningWorkspace.onIterationFocus so re-clicking the same iteration
    // still re-focuses both views (a watch here would no-op on same value).
    activeIteration.value = n
  }

  function setError(msg: string | null): void {
    error.value = msg
  }

  function toggleFocusMode(): void {
    focusMode.value = !focusMode.value
  }

  /** Full reset — e.g. when the user switches document. */
  function reset(): void {
    rawResult.value = null
    envelope.value = null
    overlay.value = null
    activeIteration.value = null
    error.value = null
    importDialogOpen.value = false
    runDialogOpen.value = false
    running.value = false
    focusMode.value = true
  }

  return {
    // state
    importDialogOpen,
    runDialogOpen,
    running,
    rawResult,
    envelope,
    overlay,
    activeIteration,
    error,
    focusMode,
    // computed
    hasTrace,
    iterations,
    presentCount,
    missingCount,
    // actions
    openImportDialog,
    closeImportDialog,
    openRunDialog,
    closeRunDialog,
    setRunning,
    setResult,
    setOverlay,
    setActiveIteration,
    setError,
    toggleFocusMode,
    reset,
  }
})
