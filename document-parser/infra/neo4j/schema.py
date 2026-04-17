"""Idempotent Neo4j schema bootstrap.

Runs at backend startup. All statements use `IF NOT EXISTS`, so calling
this multiple times is safe — it's the contract integration tests rely on.
"""

from __future__ import annotations

import logging

from infra.neo4j.driver import Neo4jDriver

logger = logging.getLogger(__name__)


CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT document_id IF NOT EXISTS "
    "FOR (d:Document) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT element_composite IF NOT EXISTS "
    "FOR (e:Element) REQUIRE (e.doc_id, e.self_ref) IS UNIQUE",
    "CREATE CONSTRAINT page_composite IF NOT EXISTS "
    "FOR (p:Page) REQUIRE (p.doc_id, p.page_no) IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
    "FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
)

INDEXES: tuple[str, ...] = (
    "CREATE INDEX element_doc IF NOT EXISTS FOR (e:Element) ON (e.doc_id)",
    "CREATE INDEX chunk_doc IF NOT EXISTS FOR (c:Chunk) ON (c.doc_id)",
)

FULLTEXT_INDEXES: tuple[str, ...] = (
    "CREATE FULLTEXT INDEX element_text IF NOT EXISTS "
    "FOR (e:Element) ON EACH [e.text]",
)


async def bootstrap_schema(neo: Neo4jDriver) -> None:
    """Create constraints and indexes required by the graph model.

    Idempotent: safe to call on every startup.
    """
    async with neo.driver.session(database=neo.database) as session:
        for stmt in (*CONSTRAINTS, *INDEXES, *FULLTEXT_INDEXES):
            await session.run(stmt)
    logger.info(
        "Neo4j schema bootstrapped (%d constraints, %d indexes, %d fulltext)",
        len(CONSTRAINTS),
        len(INDEXES),
        len(FULLTEXT_INDEXES),
    )
