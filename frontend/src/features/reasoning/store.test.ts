import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { parseImportedTrace, useReasoningStore } from './store'

describe('parseImportedTrace', () => {
  const bare = {
    answer: 'ok',
    converged: true,
    iterations: [],
  }

  it('accepts a bare RAGResult', () => {
    const parsed = parseImportedTrace(bare)
    expect(parsed?.result.answer).toBe('ok')
    expect(parsed?.envelope).toBeNull()
  })

  it('accepts a sidecar envelope and extracts the result', () => {
    const parsed = parseImportedTrace({
      job_id: 'abc',
      filename: 'x.pdf',
      result: bare,
    })
    expect(parsed?.result.answer).toBe('ok')
    expect(parsed?.envelope?.job_id).toBe('abc')
  })

  it('rejects shapes that are neither envelope nor bare RAGResult', () => {
    expect(parseImportedTrace(null)).toBeNull()
    expect(parseImportedTrace('string')).toBeNull()
    expect(parseImportedTrace({ foo: 'bar' })).toBeNull()
    expect(parseImportedTrace({ answer: 'x' })).toBeNull() // missing converged + iterations
  })
})

describe('useReasoningStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts empty', () => {
    const s = useReasoningStore()
    expect(s.hasTrace).toBe(false)
    expect(s.iterations).toEqual([])
    expect(s.presentCount).toBe(0)
  })

  it('setResult populates and resets active iteration', () => {
    const s = useReasoningStore()
    s.setActiveIteration(3)
    s.setResult({ answer: 'a', converged: true, iterations: [] }, null)
    expect(s.hasTrace).toBe(true)
    expect(s.activeIteration).toBeNull()
  })

  it('toggleFocusMode flips the flag', () => {
    const s = useReasoningStore()
    expect(s.focusMode).toBe(true)
    s.toggleFocusMode()
    expect(s.focusMode).toBe(false)
    s.toggleFocusMode()
    expect(s.focusMode).toBe(true)
  })

  it('reset restores focusMode to the default on', () => {
    const s = useReasoningStore()
    s.toggleFocusMode()
    expect(s.focusMode).toBe(false)
    s.reset()
    expect(s.focusMode).toBe(true)
  })

  it('reset clears everything including the dialog flag', () => {
    const s = useReasoningStore()
    s.openImportDialog()
    s.setResult({ answer: 'a', converged: true, iterations: [] }, null)
    s.setError('boom')
    s.reset()
    expect(s.hasTrace).toBe(false)
    expect(s.error).toBeNull()
    expect(s.importDialogOpen).toBe(false)
  })
})
