# Bounding Box Pipeline

The bbox pipeline is the core of Docling Studio's visual overlay. It transforms Docling's raw bounding box coordinates into pixel rectangles drawn on the canvas.

## The 3 Coordinate Spaces

```
 SPACE 1 — Docling (PDF points)         SPACE 2 — Normalized (PDF points)       SPACE 3 — Canvas (pixels)
 Variable origin per PDF                Always TOPLEFT                           CSS pixels × devicePixelRatio

 BOTTOMLEFT        TOPLEFT
                                              (0,0) ──────→ x                     (0,0) ──────────→ x
 y ↑                (0,0) ──→ x                │                                    │
   │  ┌───┐ t=700    │  ┌───┐ t=92             │  ┌───┐ t=92                        │  ┌─────┐ y=105
   │  │   │           │  │   │                  │  │   │                             │  │     │
   │  └───┘ b=600     │  └───┘ b=192            │  └───┘ b=192                       │  └─────┘ y=219
   │                  ↓ y                       ↓ y                                  ↓ y
 ──┴──────→ x
 (0,0)              Unit: pt PDF               Unit: pt PDF                         Unit: CSS px
```

### Space 1 — Docling Output

Docling's `BoundingBox` has 4 values `(l, t, r, b)` and a `coord_origin`:

- **BOTTOMLEFT** (standard PDF): `y=0` at the bottom of the page. `t > b` because "top" is further from origin.
- **TOPLEFT** (some extractors): `y=0` at the top. `t < b` as expected.

Unit: **PDF points** (1 pt = 1/72 inch). US Letter = 612 × 792 pt, A4 = 595 × 842 pt.

### Space 2 — Normalized (TOPLEFT)

The backend normalizes all bboxes to TOPLEFT before sending to the frontend. This is what arrives in the JSON `pages` payload.

### Space 3 — Canvas Pixels

The frontend converts PDF points to CSS pixels, then the canvas renders at `devicePixelRatio` for Retina sharpness.

## Transformation 1 — `to_topleft_list()`

**File:** `document-parser/infra/bbox.py`

Normalizes any Docling bbox to `[left, top, right, bottom]` in TOPLEFT coordinates.

```python
def to_topleft_list(bbox: BoundingBox, page_height: float) -> list[float]:
    normalized = bbox.to_top_left_origin(page_height)
    left, top, right, bottom = normalized.l, normalized.t, normalized.r, normalized.b

    # Degenerate bbox: zero or negative dimensions — skip silently.
    if right <= left or bottom <= top:
        return list(EMPTY_BBOX)  # [0, 0, 0, 0]

    return [left, top, right, bottom]
```

**Math (BOTTOMLEFT → TOPLEFT):**

```
new_top    = page_height - old_top
new_bottom = page_height - old_bottom
```

**Example** (US Letter page, 792pt):

```
Input:  l=50, t=700, r=200, b=600  (BOTTOMLEFT)

new_top    = 792 - 700 = 92     ← near the top of the page
new_bottom = 792 - 600 = 192    ← below the element

Output: [50, 92, 200, 192]      (TOPLEFT, t < b ✓)
```

!!! warning "Fallback page dimensions"
    If Docling doesn't report page dimensions (corrupted PDF), the backend falls back to US Letter (612 × 792 pt). A warning is logged. This may cause slight bbox misalignment on A4 or other formats.

## Transformation 2 — `computeScale()` + `bboxToRect()`

**File:** `frontend/src/features/analysis/bboxScaling.ts`

Maps PDF points to CSS pixels based on the displayed image size.

### Step 2a — Scale factors

```typescript
function computeScale(displayWidth, displayHeight, pageWidth, pageHeight): Scale {
  return {
    sx: displayWidth / pageWidth,    // CSS pixels per PDF point (X axis)
    sy: displayHeight / pageHeight,  // CSS pixels per PDF point (Y axis)
  }
}
```

**Example:** image rendered at 700px wide for a 612pt page:

```
sx = 700 / 612 ≈ 1.1438
sy = 907 / 792 ≈ 1.1451    (≈ same ratio when aspect is preserved)
```

### Step 2b — Bbox to pixel rectangle

```typescript
function bboxToRect(bbox: [l, t, r, b], scale: Scale): Rect {
  return {
    x: l × sx,         // left edge in pixels
    y: t × sy,         // top edge in pixels
    w: (r - l) × sx,   // width in pixels
    h: (b - t) × sy,   // height in pixels
  }
}
```

**Example** with bbox `[50, 92, 200, 192]` and `sx ≈ sy ≈ 1.14`:

```
x = 50  × 1.14 =  57 px
y = 92  × 1.14 = 105 px
w = 150 × 1.14 = 171 px
h = 100 × 1.14 = 114 px
```

## Transformation 3 — Retina Rendering

**File:** `frontend/src/features/analysis/ui/BboxOverlay.vue`

The canvas backing store is scaled by `devicePixelRatio` for crisp rendering on HiDPI screens:

```typescript
const dpr = window.devicePixelRatio || 1

// Backing store at device resolution
canvas.width  = displayWidth × dpr    // e.g. 700 × 2 = 1400
canvas.height = displayHeight × dpr

// CSS size stays the same
canvas.style.width  = displayWidth + 'px'
canvas.style.height = displayHeight + 'px'

// Scale the drawing context
ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
```

After `setTransform`, all drawing commands use CSS pixel coordinates. The canvas automatically renders them at device resolution.

```
ctx.strokeRect(57, 105, 171, 114)
→ Actual pixels on Retina 2x: (114, 210, 342, 228)
→ Visually identical but 2× sharper
```

## Complete Pipeline Summary

```
Docling BoundingBox        bbox.py              bboxScaling.ts         BboxOverlay.vue
(l, t, r, b)         → to_topleft_list() →  [l, t, r, b]  →  {x, y, w, h}  →  canvas
BOTTOMLEFT or TOPLEFT   flip Y if needed     PDF points       CSS pixels       device pixels
unit: PDF points        + validation         TOPLEFT          × (sx, sy)       × dpr
```

## Validation & Edge Cases

Both backend and frontend guard against degenerate bboxes:

| Check | Backend (`bbox.py`) | Frontend (`bboxScaling.ts`) |
|-------|--------------------|-----------------------------|
| Zero/negative width | Returns `[0,0,0,0]` | Returns `EMPTY_RECT` |
| Zero/negative height | Returns `[0,0,0,0]` | Returns `EMPTY_RECT` |
| Zero page dimensions | N/A | `computeScale` returns `{1,1}` |

A degenerate bbox results in a zero-area rectangle that the canvas doesn't draw and hit-testing ignores.
