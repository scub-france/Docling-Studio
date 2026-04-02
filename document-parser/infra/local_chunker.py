"""Local Docling chunker — runs chunking in-process using docling-core.

This adapter implements the DocumentChunker port. It deserializes a
DoclingDocument from JSON, applies the requested chunker, and returns
domain ChunkResult objects.
"""

from __future__ import annotations

import asyncio
import json
import logging

from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.document import DoclingDocument

from domain.bbox import EMPTY_BBOX, to_topleft_list
from domain.value_objects import ChunkBbox, ChunkingOptions, ChunkResult

logger = logging.getLogger(__name__)


def _chunk_sync(document_json: str, options: ChunkingOptions) -> list[ChunkResult]:
    if not document_json or not document_json.strip():
        raise ValueError("Empty document JSON — nothing to chunk")

    try:
        doc_data = json.loads(document_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed document JSON: {e}") from e

    doc = DoclingDocument.model_validate(doc_data)

    chunker = _build_chunker(options)
    results: list[ChunkResult] = []

    for chunk in chunker.chunk(doc):
        source_page = None
        token_count = 0
        bboxes: list[ChunkBbox] = []

        if hasattr(chunk, "meta") and chunk.meta and chunk.meta.doc_items:
            for doc_item in chunk.meta.doc_items:
                if not hasattr(doc_item, "prov") or not doc_item.prov:
                    continue
                for prov in doc_item.prov:
                    page_no = prov.page_no
                    if source_page is None:
                        source_page = page_no
                    if prov.bbox:
                        page_obj = doc.pages.get(page_no)
                        if page_obj:
                            bbox = to_topleft_list(prov.bbox, page_obj.size.height)
                            if bbox != EMPTY_BBOX:
                                bboxes.append(ChunkBbox(page=page_no, bbox=bbox))

        if hasattr(chunker, "tokenizer") and chunker.tokenizer:
            token_count = chunker.tokenizer.count_tokens(chunk.text)

        headings = list(chunk.meta.headings) if chunk.meta and chunk.meta.headings else []

        results.append(
            ChunkResult(
                text=chunk.text,
                headings=headings,
                source_page=source_page,
                token_count=token_count,
                bboxes=bboxes,
            )
        )

    logger.info("Chunked document into %d chunks (chunker=%s)", len(results), options.chunker_type)
    return results


def _build_chunker(options: ChunkingOptions) -> HierarchicalChunker | HybridChunker:
    if options.chunker_type == "hierarchical":
        return HierarchicalChunker()

    return HybridChunker(
        max_tokens=options.max_tokens,
        merge_peers=options.merge_peers,
        repeat_table_header=options.repeat_table_header,
    )


class LocalChunker:
    """Adapter that runs docling-core chunking locally."""

    async def chunk(
        self,
        document_json: str,
        options: ChunkingOptions,
    ) -> list[ChunkResult]:
        return await asyncio.to_thread(_chunk_sync, document_json, options)
