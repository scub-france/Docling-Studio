"""Bounding box coordinate normalization for Docling output.

Docling's BoundingBox uses two possible coordinate origins:
- TOPLEFT:    y=0 at top,    t < b  (t is smaller, closer to origin)
- BOTTOMLEFT: y=0 at bottom, t > b  (t is larger, further from origin)

The frontend canvas uses TOPLEFT coordinates. This module ensures all
bboxes are normalized to TOPLEFT [left, top, right, bottom] before
being sent to the frontend.
"""

import logging

from docling_core.types.doc.base import BoundingBox

logger = logging.getLogger(__name__)

# Sentinel value returned when a bbox is invalid or degenerate.
# A zero-area rect is safe: the frontend draws nothing and hit-testing ignores it.
EMPTY_BBOX: list[float] = [0.0, 0.0, 0.0, 0.0]


def to_topleft_list(bbox: BoundingBox, page_height: float) -> list[float]:
    """Convert a Docling BoundingBox to a [l, t, r, b] list in TOPLEFT origin.

    Validates the result: left < right and top < bottom. If the bbox is
    degenerate (zero or negative area), returns EMPTY_BBOX so the frontend
    silently skips it instead of rendering a broken rectangle.

    Args:
        bbox: Docling BoundingBox (any origin).
        page_height: Height of the page (needed for BOTTOMLEFT conversion).

    Returns:
        [left, top, right, bottom] in TOPLEFT coordinates, or EMPTY_BBOX
        if the bbox is degenerate.
    """
    normalized = bbox.to_top_left_origin(page_height)
    left, top, right, bottom = normalized.l, normalized.t, normalized.r, normalized.b

    # Degenerate bbox: zero or negative dimensions — skip silently.
    # This can happen with corrupted PDFs or edge-case Docling outputs.
    if right <= left or bottom <= top:
        logger.debug(
            "Degenerate bbox skipped: [%.1f, %.1f, %.1f, %.1f] (page_height=%.1f)",
            left,
            top,
            right,
            bottom,
            page_height,
        )
        return list(EMPTY_BBOX)

    return [left, top, right, bottom]
