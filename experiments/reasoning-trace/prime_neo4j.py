#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "neo4j>=5.20,<6",
#   "python-dotenv>=1.0",
# ]
# ///
"""
Populate Neo4j with the DoclingDocument tree + pages for one or more analysis
jobs, **without re-parsing the PDFs**. Reuses Studio's own TreeWriter so the
graph is byte-identical to what an in-UI analysis would produce.

Use when:
  - Neo4j was brought up after some docs were already analyzed (orphan graphs).
  - You want to prime a demo environment from existing SQLite state.

Usage:
    # Single job
    uv run experiments/reasoning-trace/prime_neo4j.py \\
        --job-id 722d5631-0089-44a3-a64a-7ce5b99579d3

    # All completed analyses that have a document_json but no graph yet
    uv run experiments/reasoning-trace/prime_neo4j.py --all-missing

Env (defaults match docker-compose.dev.yml):
    NEO4J_URI       default bolt://localhost:7687
    NEO4J_USER      default neo4j
    NEO4J_PASSWORD  default changeme
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DB_PATH = REPO / "document-parser" / "data" / "docling_studio.db"

# Studio's own TreeWriter lives in document-parser/infra/neo4j. Import it by
# adding document-parser to sys.path — this keeps us byte-identical with what
# the live backend writes, instead of re-implementing the walk.
sys.path.insert(0, str(REPO / "document-parser"))


def _fetch_row(job_id: str) -> tuple[str, str, str] | None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        """
        SELECT aj.document_id, d.filename, aj.document_json
        FROM analysis_jobs aj
        JOIN documents d ON d.id = aj.document_id
        WHERE aj.id = ? AND aj.document_json IS NOT NULL
        """,
        (job_id,),
    ).fetchone()
    con.close()
    return (row["document_id"], row["filename"], row["document_json"]) if row else None


def _fetch_all_completed() -> list[tuple[str, str, str, str]]:
    """Latest completed analysis per document that has a document_json."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT aj.id, aj.document_id, d.filename, aj.document_json
        FROM analysis_jobs aj
        JOIN documents d ON d.id = aj.document_id
        WHERE aj.document_json IS NOT NULL
          AND aj.status = 'COMPLETED'
        GROUP BY aj.document_id
        HAVING MAX(aj.completed_at)
        """,
    ).fetchall()
    con.close()
    return [(r["id"], r["document_id"], r["filename"], r["document_json"]) for r in rows]


async def prime(job_id: str, doc_id: str, filename: str, document_json: str) -> None:
    # Imports deferred until after sys.path is patched.
    from infra.neo4j import bootstrap_schema, close_driver, get_driver, write_document

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD", "changeme")

    neo = await get_driver(uri, user, pwd)
    try:
        # Schema is idempotent; safe to run every time.
        await bootstrap_schema(neo)
        result = await write_document(
            neo,
            doc_id=doc_id,
            filename=filename,
            document_json=document_json,
        )
        print(
            f"  ✓ {doc_id[:8]}  {filename[:40]:<40}  "
            f"elements={result.element_count} pages={result.page_count}"
        )
    finally:
        await close_driver()


async def main_async() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--job-id", help="analysis_jobs.id to prime")
    g.add_argument(
        "--all-missing",
        action="store_true",
        help="prime every completed analysis with a document_json (latest per doc)",
    )
    args = p.parse_args()

    if not DB_PATH.exists():
        sys.exit(f"SQLite DB not found at {DB_PATH}")

    started = datetime.now(tz=UTC)
    if args.job_id:
        row = _fetch_row(args.job_id)
        if row is None:
            sys.exit(f"No analysis with id {args.job_id} or no document_json")
        doc_id, filename, document_json = row
        print(f"→ Priming Neo4j for job {args.job_id[:8]} (doc {doc_id[:8]})")
        await prime(args.job_id, doc_id, filename, document_json)
    else:
        rows = _fetch_all_completed()
        print(f"→ Priming Neo4j for {len(rows)} document(s)")
        for job_id, doc_id, filename, document_json in rows:
            try:
                await prime(job_id, doc_id, filename, document_json)
            except Exception as e:
                print(f"  ✗ {doc_id[:8]}  {filename[:40]:<40}  FAILED: {e}")

    elapsed = (datetime.now(tz=UTC) - started).total_seconds()
    print(f"Done in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main_async())
