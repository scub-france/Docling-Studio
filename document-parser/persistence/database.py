"""SQLite database management — async via aiosqlite."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "./data/docling_studio.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id              TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    content_type    TEXT,
    file_size       INTEGER,
    page_count      INTEGER,
    storage_path    TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id                TEXT PRIMARY KEY,
    document_id       TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status            TEXT NOT NULL DEFAULT 'PENDING',
    content_markdown  TEXT,
    content_html      TEXT,
    pages_json        TEXT,
    document_json     TEXT,
    chunks_json       TEXT,
    error_message     TEXT,
    started_at        TEXT,
    completed_at      TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_created_at ON analysis_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
"""


_MIGRATIONS = [
    ("document_json", "ALTER TABLE analysis_jobs ADD COLUMN document_json TEXT"),
    ("chunks_json", "ALTER TABLE analysis_jobs ADD COLUMN chunks_json TEXT"),
    ("progress_current", "ALTER TABLE analysis_jobs ADD COLUMN progress_current INTEGER"),
    ("progress_total", "ALTER TABLE analysis_jobs ADD COLUMN progress_total INTEGER"),
]


async def _run_migrations(db: aiosqlite.Connection) -> None:
    """Add columns that may be missing in older databases."""
    cursor = await db.execute("PRAGMA table_info(analysis_jobs)")
    existing = {row[1] for row in await cursor.fetchall()}
    for col_name, ddl in _MIGRATIONS:
        if col_name not in existing:
            await db.execute(ddl)
            logger.info("Migration: added column %s to analysis_jobs", col_name)
    await db.commit()


async def init_db() -> None:
    """Create database file and tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await _run_migrations(db)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def get_db() -> aiosqlite.Connection:
    """Open a new database connection with row factory and FK enforcement."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


@asynccontextmanager
async def get_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Context manager that opens and auto-closes a database connection."""
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()
