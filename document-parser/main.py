"""Docling Studio — unified FastAPI backend.

Single service replacing both the Spring Boot backend and the document parser.
Provides document management (upload, CRUD), analysis orchestration (async Docling
processing), and PDF preview — all backed by SQLite.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from persistence.database import init_db
from api.documents import router as documents_router
from api.analyses import router as analyses_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database. Shutdown: nothing special needed."""
    await init_db()
    logger.info("Docling Studio backend ready")
    yield


app = FastAPI(
    title="Docling Studio",
    description="Document analysis studio powered by Docling",
    lifespan=lifespan,
)

# CORS — configurable via env, defaults for local dev
allowed_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount routers
app.include_router(documents_router)
app.include_router(analyses_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
