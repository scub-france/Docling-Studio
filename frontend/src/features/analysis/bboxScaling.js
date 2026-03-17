/**
 * Bbox scaling utilities for mapping Docling TOPLEFT coordinates
 * to canvas pixel coordinates.
 *
 * Docling bbox format (after backend normalization): [l, t, r, b]
 * All values are in page coordinate space (points, 1pt = 1/72 inch).
 * Origin: top-left (y=0 at top of page).
 *
 * The preview image is a faithful rasterization of the PDF page.
 * CSS `max-width: 100%; height: auto` preserves the aspect ratio,
 * so sx and sy are always equal. We compute both for completeness.
 */

/**
 * Compute scale factors from page coordinates to displayed pixels.
 *
 * @param {number} displayWidth  - img.clientWidth (CSS pixels)
 * @param {number} displayHeight - img.clientHeight (CSS pixels)
 * @param {number} pageWidth     - Page width in Docling points
 * @param {number} pageHeight    - Page height in Docling points
 * @returns {{ sx: number, sy: number }}
 */
export function computeScale(displayWidth, displayHeight, pageWidth, pageHeight) {
  return {
    sx: displayWidth / pageWidth,
    sy: displayHeight / pageHeight,
  }
}

/**
 * Convert a Docling bbox [l, t, r, b] to a canvas rect { x, y, w, h }.
 *
 * @param {number[]} bbox  - [left, top, right, bottom] in page points
 * @param {{ sx: number, sy: number }} scale
 * @returns {{ x: number, y: number, w: number, h: number }}
 */
export function bboxToRect(bbox, scale) {
  const [l, t, r, b] = bbox
  return {
    x: l * scale.sx,
    y: t * scale.sy,
    w: (r - l) * scale.sx,
    h: (b - t) * scale.sy,
  }
}

/**
 * Test if a point (px, py) falls inside a rect.
 *
 * @param {number} px
 * @param {number} py
 * @param {{ x: number, y: number, w: number, h: number }} rect
 * @returns {boolean}
 */
export function pointInRect(px, py, rect) {
  return px >= rect.x && px <= rect.x + rect.w &&
         py >= rect.y && py <= rect.y + rect.h
}
