"""Docling Studio — unified FastAPI backend.

Single service providing document management (upload, CRUD), analysis
orchestration (async Docling processing), and PDF preview — all backed
by SQLite.

Conversion engine is selected via CONVERSION_ENGINE env var:
- "local"  → Docling runs in-process as a Python library (default)
- "remote" → delegates to a Docling Serve instance via HTTP
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyses import router as analyses_router
from api.documents import router as documents_router
from api.ingestion import router as ingestion_router
from api.schemas import HealthResponse
from infra.rate_limiter import RateLimiterMiddleware
from infra.settings import settings
from persistence.analysis_repo import SqliteAnalysisRepository
from persistence.database import get_connection, init_db
from persistence.document_repo import SqliteDocumentRepository
from services.analysis_service import AnalysisConfig, AnalysisService
from services.document_service import DocumentConfig, DocumentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _build_converter():
    """Build the converter adapter based on configuration."""
    if settings.conversion_engine == "remote":
        from infra.serve_converter import ServeConverter

        logger.info("Using remote Docling Serve at %s", settings.docling_serve_url)
        return ServeConverter(
            base_url=settings.docling_serve_url,
            api_key=settings.docling_serve_api_key,
        )
    else:
        from infra.local_converter import LocalConverter

        logger.info("Using local Docling converter")
        return LocalConverter()


def _build_chunker():
    """Build the chunker adapter — only available in local mode."""
    if settings.conversion_engine == "local":
        from infra.local_chunker import LocalChunker

        return LocalChunker()
    return None


def _build_repos() -> tuple[SqliteDocumentRepository, SqliteAnalysisRepository]:
    return SqliteDocumentRepository(), SqliteAnalysisRepository()


def _build_analysis_service(
    document_repo: SqliteDocumentRepository,
    analysis_repo: SqliteAnalysisRepository,
) -> AnalysisService:
    converter = _build_converter()
    chunker = _build_chunker()
    config = AnalysisConfig(
        default_table_mode=settings.default_table_mode,
        batch_page_size=settings.batch_page_size,
    )
    return AnalysisService(
        converter=converter,
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        chunker=chunker,
        conversion_timeout=settings.conversion_timeout,
        max_concurrent=settings.max_concurrent_analyses,
        config=config,
    )


def _build_document_service(
    document_repo: SqliteDocumentRepository,
    analysis_repo: SqliteAnalysisRepository,
) -> DocumentService:
    config = DocumentConfig(
        upload_dir=settings.upload_dir,
        max_file_size_mb=settings.max_file_size_mb,
        max_page_count=settings.max_page_count,
    )
    return DocumentService(
        document_repo=document_repo,
        analysis_repo=analysis_repo,
        config=config,
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------


def _build_ingestion_service(
    document_repo: SqliteDocumentRepository,
    analysis_repo: SqliteAnalysisRepository,
):
    """Build ingestion service if OpenSearch + embedding are configured."""
    if not settings.opensearch_url or not settings.embedding_url:
        logger.info(
            "Ingestion pipeline disabled (OPENSEARCH_URL=%r, EMBEDDING_URL=%r)",
            settings.opensearch_url,
            settings.embedding_url,
        )
        return None

    from infra.embedding_client import EmbeddingClient
    from infra.opensearch_store import OpenSearchStore
    from services.ingestion_service import IngestionService

    embedding_svc = EmbeddingClient(settings.embedding_url)
    vector_store = OpenSearchStore(hosts=[settings.opensearch_url])
    logger.info(
        "Ingestion pipeline enabled (opensearch=%s, embedding=%s)",
        settings.opensearch_url,
        settings.embedding_url,
    )
    return IngestionService(
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        embedding_svc=embedding_svc,
        vector_store=vector_store,
        embedding_dimension=settings.embedding_dimension,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    document_repo, analysis_repo = _build_repos()
    app.state.analysis_service = _build_analysis_service(document_repo, analysis_repo)
    app.state.document_service = _build_document_service(document_repo, analysis_repo)
    app.state.ingestion_service = _build_ingestion_service(document_repo, analysis_repo)
    logger.info("Docling Studio backend ready (engine=%s)", settings.conversion_engine)
    yield


app = FastAPI(
    title="Docling Studio",
    description="Document analysis studio powered by Docling",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
if settings.rate_limit_rpm > 0:
    app.add_middleware(
        RateLimiterMiddleware,
        requests_per_window=settings.rate_limit_rpm,
        window_seconds=60,
    )

app.include_router(documents_router)
app.include_router(analyses_router)
app.include_router(ingestion_router)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint — verifies database connectivity."""
    db_status = "ok"
    try:
        async with get_connection() as db:
            await db.execute("SELECT 1")
    except Exception:
        db_status = "error"
        logger.warning("Health check: database unreachable", exc_info=True)

    status = "ok" if db_status == "ok" else "degraded"
    return HealthResponse(
        status=status,
        version=settings.app_version,
        engine=settings.conversion_engine,
        deployment_mode=settings.deployment_mode,
        database=db_status,
        max_page_count=settings.max_page_count if settings.max_page_count > 0 else None,
        max_file_size_mb=settings.max_file_size_mb if settings.max_file_size_mb > 0 else None,
    )
