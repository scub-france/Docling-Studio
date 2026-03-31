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
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyses import router as analyses_router
from api.documents import router as documents_router
from infra.settings import Settings
from persistence.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings & dependency wiring
# ---------------------------------------------------------------------------

settings = Settings.from_env()


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


def _build_analysis_service():
    from services.analysis_service import AnalysisService
    converter = _build_converter()
    return AnalysisService(
        converter=converter,
        conversion_timeout=settings.conversion_timeout,
    )


# Singleton service instance — imported by API routers
analysis_service = _build_analysis_service()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "engine": settings.conversion_engine}
