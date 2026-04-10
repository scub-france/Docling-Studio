"""Ingestion service — orchestrates the full Docling → embedding → OpenSearch pipeline.

Pipeline stages:
    1. Load analysis job + document metadata
    2. Parse chunks from the completed job
    3. Generate embeddings for each chunk
    4. Idempotently index chunks in OpenSearch

Idempotency: existing chunks for the document are deleted before re-indexing,
so re-ingesting a document always produces a clean, up-to-date index.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.models import AnalysisStatus
from domain.vector_schema import (
    DEFAULT_INDEX_NAME,
    ChunkBboxEntry,
    ChunkOrigin,
    IndexedChunk,
    build_index_mapping,
)

if TYPE_CHECKING:
    from domain.ports import (
        AnalysisRepository,
        DocumentRepository,
        EmbeddingService,
        VectorStore,
    )

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    """Result returned by a successful ingestion run."""

    doc_id: str
    chunks_indexed: int
    embedding_dimension: int


class IngestionError(Exception):
    """Raised when the ingestion pipeline cannot complete."""


class IngestionService:
    """Orchestrates the full ingestion pipeline for a single analysis job."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        document_repo: DocumentRepository,
        embedding_svc: EmbeddingService,
        vector_store: VectorStore,
        *,
        index_name: str = DEFAULT_INDEX_NAME,
        embedding_dimension: int = 384,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._document_repo = document_repo
        self._embedding_svc = embedding_svc
        self._vector_store = vector_store
        self._index_name = index_name
        self._embedding_dimension = embedding_dimension

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest(self, job_id: str) -> IngestionResult:
        """Run the full ingestion pipeline for the given analysis job.

        Args:
            job_id: ID of a COMPLETED analysis job that has chunks.

        Returns:
            IngestionResult with doc_id and number of indexed chunks.

        Raises:
            IngestionError: if any pipeline stage fails.
        """
        logger.info("Ingestion started for job %s", job_id)

        # --- Stage 1: load job ---
        job = await self._analysis_repo.find_by_id(job_id)
        if job is None:
            raise IngestionError(f"Analysis job not found: {job_id}")
        if job.status != AnalysisStatus.COMPLETED:
            raise IngestionError(
                f"Job {job_id} is not COMPLETED (status={job.status}). Run analysis first."
            )
        if not job.chunks_json:
            raise IngestionError(f"Job {job_id} has no chunks. Run chunking first.")

        doc = await self._document_repo.find_by_id(job.document_id)
        if doc is None:
            raise IngestionError(f"Document not found: {job.document_id}")

        logger.info("Loaded job %s — document: %s", job_id, doc.filename)

        # --- Stage 2: parse chunks ---
        try:
            raw_chunks: list[dict] = json.loads(job.chunks_json)
        except json.JSONDecodeError as exc:
            raise IngestionError(f"Invalid chunks_json in job {job_id}") from exc

        if not raw_chunks:
            raise IngestionError(f"Job {job_id} has empty chunk list. Chunk first.")

        texts = [c.get("text", "") for c in raw_chunks]
        logger.info("Parsed %d chunks from job %s", len(texts), job_id)

        # --- Stage 3: generate embeddings ---
        try:
            embeddings = await self._embedding_svc.embed(texts)
        except Exception as exc:
            raise IngestionError(f"Embedding generation failed: {exc}") from exc

        if len(embeddings) != len(texts):
            raise IngestionError(
                f"Embedding dimension mismatch: got {len(embeddings)} vectors for {len(texts)} texts"
            )

        # Detect embedding dimension from the first non-empty vector
        detected_dim = self._embedding_dimension
        for vec in embeddings:
            if vec:
                detected_dim = len(vec)
                break

        logger.info("Generated %d embeddings (dim=%d)", len(embeddings), detected_dim)

        # --- Stage 4: ensure index exists ---
        mapping = build_index_mapping(detected_dim)
        try:
            await self._vector_store.ensure_index(self._index_name, mapping)
        except Exception as exc:
            raise IngestionError(f"Failed to ensure index: {exc}") from exc

        # --- Stage 4b: delete existing chunks (idempotency) ---
        try:
            deleted = await self._vector_store.delete_document(self._index_name, doc.id)
            if deleted:
                logger.info("Deleted %d existing chunks for document %s", deleted, doc.id)
        except Exception as exc:
            raise IngestionError(f"Failed to delete existing chunks: {exc}") from exc

        # --- Stage 5: build IndexedChunk list ---
        origin = ChunkOrigin(
            binary_hash=doc.id,  # use doc id as stable identifier
            filename=doc.filename,
        )

        indexed_chunks: list[IndexedChunk] = []
        for i, (raw, emb) in enumerate(zip(raw_chunks, embeddings, strict=True)):
            bboxes = [
                ChunkBboxEntry(
                    page=b.get("page", 0),
                    x=b["bbox"][0] if b.get("bbox") else 0.0,
                    y=b["bbox"][1] if b.get("bbox") else 0.0,
                    w=(b["bbox"][2] - b["bbox"][0])
                    if b.get("bbox") and len(b["bbox"]) >= 4
                    else 0.0,
                    h=(b["bbox"][3] - b["bbox"][1])
                    if b.get("bbox") and len(b["bbox"]) >= 4
                    else 0.0,
                )
                for b in raw.get("bboxes", [])
            ]

            chunk = IndexedChunk(
                doc_id=doc.id,
                filename=doc.filename,
                content=raw.get("text", ""),
                embedding=emb,
                chunk_index=i,
                chunk_type="text",
                page_number=raw.get("sourcePage") or 0,
                bboxes=bboxes,
                headings=raw.get("headings", []),
                doc_items=[],
                origin=origin,
            )
            indexed_chunks.append(chunk)

        # --- Stage 6: bulk index ---
        try:
            indexed_count = await self._vector_store.index_chunks(self._index_name, indexed_chunks)
        except Exception as exc:
            raise IngestionError(f"Bulk indexing failed: {exc}") from exc

        logger.info(
            "Ingestion complete — %d/%d chunks indexed for document %s",
            indexed_count,
            len(indexed_chunks),
            doc.id,
        )
        return IngestionResult(
            doc_id=doc.id,
            chunks_indexed=indexed_count,
            embedding_dimension=detected_dim,
        )

    async def delete(self, doc_id: str) -> int:
        """Remove all indexed chunks for a document.

        Returns:
            Number of chunks deleted.
        """
        logger.info("Deleting indexed chunks for document %s", doc_id)
        try:
            deleted = await self._vector_store.delete_document(self._index_name, doc_id)
        except Exception as exc:
            raise IngestionError(f"Failed to delete from index: {exc}") from exc
        logger.info("Deleted %d chunks for document %s", deleted, doc_id)
        return deleted
