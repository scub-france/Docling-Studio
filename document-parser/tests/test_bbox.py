"""Tests for bbox coordinate normalization.

These tests cover the core bbox pipeline — the most critical part of the
visual rendering. Every edge case matters because a broken bbox means
misaligned overlays in the UI.
"""

import pytest
from docling_core.types.doc.base import BoundingBox, CoordOrigin

from domain.bbox import EMPTY_BBOX, to_topleft_list


# ---------------------------------------------------------------------------
# Standard conversions
# ---------------------------------------------------------------------------

class TestToTopleftListStandard:
    """Normal bbox conversions (happy path)."""

    def test_topleft_origin_unchanged(self):
        """TOPLEFT bbox should pass through unchanged."""
        bbox = BoundingBox(l=10, t=20, r=100, b=80, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [10, 20, 100, 80]

    def test_bottomleft_origin_converted(self):
        """BOTTOMLEFT bbox should have y-coordinates flipped."""
        bbox = BoundingBox(l=50, t=700, r=200, b=600, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=792.0)

        # After conversion: new_t = 792 - 700 = 92, new_b = 792 - 600 = 192
        assert result[0] == 50       # l unchanged
        assert result[1] == pytest.approx(92.0)   # t = page_height - old_t
        assert result[2] == 200      # r unchanged
        assert result[3] == pytest.approx(192.0)   # b = page_height - old_b

    def test_result_has_positive_dimensions(self):
        """Converted bbox should always have b > t (positive height)."""
        bbox = BoundingBox(l=10, t=500, r=300, b=100, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=800.0)

        left, t, r, b = result
        assert r > left, "width should be positive"
        assert b > t, "height should be positive"

    def test_full_page_bbox_bottomleft(self):
        """A bbox covering the full page in BOTTOMLEFT origin."""
        bbox = BoundingBox(l=0, t=792, r=612, b=0, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [0, 0, 612, 792]

    def test_full_page_bbox_topleft(self):
        """A bbox covering the full page in TOPLEFT origin."""
        bbox = BoundingBox(l=0, t=0, r=612, b=792, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [0, 0, 612, 792]


# ---------------------------------------------------------------------------
# Page format variations
# ---------------------------------------------------------------------------

class TestPageFormats:
    """Verify correct conversion across different page sizes."""

    def test_a4_page(self):
        """A4 page (595.28 × 841.89 pt) — most common non-US format."""
        page_height = 841.89
        bbox = BoundingBox(l=72, t=769.89, r=523.28, b=72, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=page_height)

        assert result[0] == 72
        assert result[1] == pytest.approx(page_height - 769.89)  # ~72
        assert result[2] == 523.28
        assert result[3] == pytest.approx(page_height - 72)  # ~769.89

    def test_a3_page(self):
        """A3 page (841.89 × 1190.55 pt)."""
        page_height = 1190.55
        bbox = BoundingBox(l=0, t=1190.55, r=841.89, b=0, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=page_height)
        assert result == pytest.approx([0, 0, 841.89, 1190.55])

    def test_legal_page(self):
        """US Legal page (612 × 1008 pt)."""
        page_height = 1008.0
        bbox = BoundingBox(l=50, t=50, r=562, b=958, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=page_height)
        assert result == [50, 50, 562, 958]

    def test_landscape_page(self):
        """Landscape orientation (width > height)."""
        page_height = 612.0  # Letter landscape
        bbox = BoundingBox(l=100, t=500, r=700, b=100, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=page_height)

        left, top, right, bottom = result
        assert right > left
        assert bottom > top
        assert top == pytest.approx(612.0 - 500.0)  # 112
        assert bottom == pytest.approx(612.0 - 100.0)  # 512


# ---------------------------------------------------------------------------
# Degenerate / edge-case bboxes
# ---------------------------------------------------------------------------

class TestDegenerateBboxes:
    """Bboxes that are invalid or degenerate should return EMPTY_BBOX."""

    def test_zero_width_returns_empty(self):
        """A bbox with l == r (zero width) is degenerate."""
        bbox = BoundingBox(l=100, t=20, r=100, b=80, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == EMPTY_BBOX

    def test_zero_height_returns_empty(self):
        """A bbox with t == b (zero height) is degenerate."""
        bbox = BoundingBox(l=10, t=50, r=100, b=50, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == EMPTY_BBOX

    def test_inverted_lr_returns_empty(self):
        """A bbox where l > r (inverted x) is degenerate."""
        bbox = BoundingBox(l=200, t=20, r=100, b=80, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == EMPTY_BBOX

    def test_inverted_tb_topleft_returns_empty(self):
        """A TOPLEFT bbox where t > b (inverted y) is degenerate."""
        bbox = BoundingBox(l=10, t=100, r=200, b=50, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == EMPTY_BBOX

    def test_point_bbox_returns_empty(self):
        """A zero-area point bbox (l==r, t==b) is degenerate."""
        bbox = BoundingBox(l=100, t=200, r=100, b=200, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == EMPTY_BBOX

    def test_empty_bbox_is_not_mutated(self):
        """Each call returns a fresh list — no shared mutable state."""
        bbox = BoundingBox(l=100, t=20, r=100, b=80, coord_origin=CoordOrigin.TOPLEFT)
        result1 = to_topleft_list(bbox, page_height=792.0)
        result2 = to_topleft_list(bbox, page_height=792.0)
        assert result1 == result2
        assert result1 is not result2  # different list instances


# ---------------------------------------------------------------------------
# Precision and boundary values
# ---------------------------------------------------------------------------

class TestPrecision:
    """Floating-point precision and edge values."""

    def test_very_small_bbox(self):
        """A tiny but valid bbox (e.g. a period character)."""
        bbox = BoundingBox(l=100.0, t=200.0, r=100.5, b=200.5, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [100.0, 200.0, 100.5, 200.5]

    def test_fractional_coordinates(self):
        """Docling often returns sub-point precision."""
        bbox = BoundingBox(l=72.34, t=145.67, r=540.12, b=200.89, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=842.0)
        assert result == pytest.approx([72.34, 145.67, 540.12, 200.89])

    def test_bbox_at_page_origin(self):
        """Bbox starting at (0,0) — valid for elements at the very top-left."""
        bbox = BoundingBox(l=0, t=0, r=50, b=30, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [0, 0, 50, 30]

    def test_bbox_at_page_bottom_right(self):
        """Bbox at the very bottom-right corner of the page."""
        bbox = BoundingBox(l=500, t=750, r=612, b=792, coord_origin=CoordOrigin.TOPLEFT)
        result = to_topleft_list(bbox, page_height=792.0)
        assert result == [500, 750, 612, 792]

    def test_bottomleft_near_page_edge(self):
        """BOTTOMLEFT bbox near the bottom of the page (small y values)."""
        bbox = BoundingBox(l=50, t=30, r=200, b=10, coord_origin=CoordOrigin.BOTTOMLEFT)
        result = to_topleft_list(bbox, page_height=792.0)

        # Converted: top = 792-30 = 762, bottom = 792-10 = 782
        assert result[1] == pytest.approx(762.0)
        assert result[3] == pytest.approx(782.0)
