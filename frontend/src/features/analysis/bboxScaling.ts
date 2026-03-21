import type { Scale, Rect } from '../../shared/types'

export function computeScale(
  displayWidth: number,
  displayHeight: number,
  pageWidth: number,
  pageHeight: number,
): Scale {
  return {
    sx: displayWidth / pageWidth,
    sy: displayHeight / pageHeight,
  }
}

export function bboxToRect(bbox: [number, number, number, number], scale: Scale): Rect {
  const [l, t, r, b] = bbox
  return {
    x: l * scale.sx,
    y: t * scale.sy,
    w: (r - l) * scale.sx,
    h: (b - t) * scale.sy,
  }
}

export function pointInRect(px: number, py: number, rect: Rect): boolean {
  return px >= rect.x && px <= rect.x + rect.w && py >= rect.y && py <= rect.y + rect.h
}
