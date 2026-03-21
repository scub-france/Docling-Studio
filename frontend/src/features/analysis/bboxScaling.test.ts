import { describe, it, expect } from 'vitest'
import { computeScale, bboxToRect, pointInRect } from './bboxScaling'

describe('computeScale', () => {
  it('returns 1:1 when display matches page', () => {
    const s = computeScale(612, 792, 612, 792)
    expect(s.sx).toBe(1)
    expect(s.sy).toBe(1)
  })

  it('scales proportionally', () => {
    const s = computeScale(306, 396, 612, 792)
    expect(s.sx).toBeCloseTo(0.5)
    expect(s.sy).toBeCloseTo(0.5)
  })

  it('sx equals sy when aspect ratio is preserved', () => {
    // Image at 150 DPI displayed at 700px wide
    const pageW = 612, pageH = 792
    const displayW = 700
    const displayH = displayW * pageH / pageW // preserves ratio
    const s = computeScale(displayW, displayH, pageW, pageH)
    expect(s.sx).toBeCloseTo(s.sy, 5)
  })
})

describe('bboxToRect', () => {
  it('maps page coordinates to pixel rect at scale 1', () => {
    const scale = { sx: 1, sy: 1 }
    const rect = bboxToRect([10, 20, 110, 80], scale)
    expect(rect).toEqual({ x: 10, y: 20, w: 100, h: 60 })
  })

  it('scales correctly at 2x', () => {
    const scale = { sx: 2, sy: 2 }
    const rect = bboxToRect([10, 20, 60, 70], scale)
    expect(rect).toEqual({ x: 20, y: 40, w: 100, h: 100 })
  })

  it('handles fractional scales', () => {
    const scale = { sx: 0.5, sy: 0.5 }
    const rect = bboxToRect([100, 200, 300, 400], scale)
    expect(rect.x).toBeCloseTo(50)
    expect(rect.y).toBeCloseTo(100)
    expect(rect.w).toBeCloseTo(100)
    expect(rect.h).toBeCloseTo(100)
  })

  it('end-to-end: full page bbox fills display', () => {
    const scale = computeScale(700, 907.84, 612, 792)
    const rect = bboxToRect([0, 0, 612, 792], scale)
    expect(rect.x).toBeCloseTo(0)
    expect(rect.y).toBeCloseTo(0)
    expect(rect.w).toBeCloseTo(700)
    expect(rect.h).toBeCloseTo(907.84, 0)
  })
})

describe('pointInRect', () => {
  const rect = { x: 10, y: 20, w: 100, h: 60 }

  it('returns true for point inside', () => {
    expect(pointInRect(50, 50, rect)).toBe(true)
  })

  it('returns true for point on edge', () => {
    expect(pointInRect(10, 20, rect)).toBe(true)
    expect(pointInRect(110, 80, rect)).toBe(true)
  })

  it('returns false for point outside', () => {
    expect(pointInRect(5, 50, rect)).toBe(false)
    expect(pointInRect(50, 15, rect)).toBe(false)
    expect(pointInRect(115, 50, rect)).toBe(false)
  })
})
