import { describe, expect, it } from 'vitest'

import { ALL_MODES, DEFAULT_MODE, isDocMode, parseMode } from './modes'

describe('isDocMode', () => {
  it.each(['parse', 'chunk'])('accepts %s', (value) => {
    expect(isDocMode(value)).toBe(true)
  })

  it.each([undefined, null, '', 'foo', 'ask', 'linked', 'chunks', 'inspect', 42, {}, []])(
    'rejects %s',
    (value) => {
      expect(isDocMode(value)).toBe(false)
    },
  )
})

describe('parseMode', () => {
  it('returns the default for missing or unknown values', () => {
    expect(parseMode(undefined)).toBe(DEFAULT_MODE)
    expect(parseMode(null)).toBe(DEFAULT_MODE)
    expect(parseMode('garbage')).toBe(DEFAULT_MODE)
    expect(parseMode(['parse'])).toBe(DEFAULT_MODE)
  })

  it.each(['parse', 'chunk'] as const)('respects %s', (mode) => {
    expect(parseMode(mode)).toBe(mode)
  })

  it('maps legacy aliases to the current mode names', () => {
    expect(parseMode('linked')).toBe('chunk')
    expect(parseMode('chunks')).toBe('chunk')
    expect(parseMode('inspect')).toBe('parse')
  })
})

describe('ALL_MODES', () => {
  it('lists every mode exactly once', () => {
    expect(new Set(ALL_MODES).size).toBe(ALL_MODES.length)
    expect(ALL_MODES).toContain('parse')
    expect(ALL_MODES).toContain('chunk')
  })

  it('puts parse first (default landing)', () => {
    expect(ALL_MODES[0]).toBe('parse')
  })
})
