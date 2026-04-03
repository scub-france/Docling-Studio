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
from infra.settings import settings
from persistence.database import init_db
from services.analysis_service import AnalysisService

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


def _build_analysis_service() -> AnalysisService:
    converter = _build_converter()
    chunker = _build_chunker()
    return AnalysisService(
        converter=converter,
        chunker=chunker,
        conversion_timeout=settings.conversion_timeout,
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    app.state.analysis_service = _build_analysis_service()
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

app.include_router(documents_router)
app.include_router(analyses_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "engine": settings.conversion_engine,
    }
