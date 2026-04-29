import { describe, expect, it } from 'vitest'

import { ALL_MODES, DEFAULT_MODE, isDocMode, parseMode } from './modes'

describe('isDocMode', () => {
  it.each(['ask', 'inspect', 'chunks'])('accepts %s', (value) => {
    expect(isDocMode(value)).toBe(true)
  })

  it.each([undefined, null, '', 'foo', 42, {}, []])('rejects %s', (value) => {
    expect(isDocMode(value)).toBe(false)
  })
})

describe('parseMode', () => {
  it('returns the default for missing or unknown values', () => {
    expect(parseMode(undefined)).toBe(DEFAULT_MODE)
    expect(parseMode(null)).toBe(DEFAULT_MODE)
    expect(parseMode('garbage')).toBe(DEFAULT_MODE)
    expect(parseMode(['chunks'])).toBe(DEFAULT_MODE) // arrays not accepted
  })

  it.each(['ask', 'inspect', 'chunks'] as const)('respects %s', (mode) => {
    expect(parseMode(mode)).toBe(mode)
  })
})

describe('ALL_MODES', () => {
  it('lists every mode exactly once', () => {
    expect(new Set(ALL_MODES).size).toBe(ALL_MODES.length)
    expect(ALL_MODES).toContain('ask')
    expect(ALL_MODES).toContain('inspect')
    expect(ALL_MODES).toContain('chunks')
  })
})
