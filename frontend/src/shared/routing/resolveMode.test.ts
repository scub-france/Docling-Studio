import { describe, expect, it } from 'vitest'

import type { DocMode } from './modes'
import { MODE_PRIORITY, resolveMode } from './resolveMode'

const allEnabled: Record<DocMode, boolean> = { parse: true, chunk: true, ingest: true }
const allDisabled: Record<DocMode, boolean> = { parse: false, chunk: false, ingest: false }

describe('resolveMode', () => {
  it('returns the requested mode when it is enabled', () => {
    expect(resolveMode('parse', allEnabled)).toBe('parse')
    expect(resolveMode('chunk', allEnabled)).toBe('chunk')
    expect(resolveMode('ingest', allEnabled)).toBe('ingest')
  })

  it('falls back to the highest-priority enabled mode when the requested one is disabled', () => {
    expect(resolveMode('parse', { parse: false, chunk: true, ingest: true })).toBe('chunk')
    expect(resolveMode('chunk', { parse: true, chunk: false, ingest: true })).toBe('parse')
    expect(resolveMode('ingest', { parse: true, chunk: false, ingest: false })).toBe('parse')
  })

  it('honours the priority order parse > chunk > ingest', () => {
    expect(resolveMode(undefined, allEnabled)).toBe('parse')
    expect(resolveMode(undefined, { parse: false, chunk: true, ingest: true })).toBe('chunk')
    expect(resolveMode(undefined, { parse: false, chunk: false, ingest: true })).toBe('ingest')
  })

  it('returns null when no mode is enabled', () => {
    expect(resolveMode('parse', allDisabled)).toBeNull()
    expect(resolveMode(undefined, allDisabled)).toBeNull()
  })

  it('handles missing requested gracefully', () => {
    expect(resolveMode(undefined, allEnabled)).toBe('parse')
  })

  it('exposes the priority in the right order', () => {
    expect(MODE_PRIORITY).toEqual(['parse', 'chunk', 'ingest'])
  })
})
