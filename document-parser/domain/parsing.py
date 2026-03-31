"""Backward-compatible re-exports for domain.parsing.

After the hexagonal architecture refactoring:
- Value objects moved to domain.value_objects
- Docling implementation moved to infra.local_converter

This module re-exports the public names so existing code and tests
that import from domain.parsing continue to work.
"""

from __future__ import annotations

from domain.value_objects import (  # noqa: F401
    ConversionOptions,
    ConversionResult,
    PageDetail,
    PageElement,
)
from infra.local_converter import (
    _build_docling_converter,
    _convert_sync,
    _extract_pages_detail as extract_pages_detail,  # noqa: F401
    _get_default_converter as get_default_converter,  # noqa: F401
)


def build_converter(options: ConversionOptions | None = None):
    """Build a Docling DocumentConverter (backward-compatible signature)."""
    return _build_docling_converter(options or ConversionOptions())


def convert_document(file_path: str, options: ConversionOptions | None = None) -> ConversionResult:
    """Convert a document synchronously (backward-compatible signature)."""
    return _convert_sync(file_path, options or ConversionOptions())
