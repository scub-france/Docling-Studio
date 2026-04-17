"""Async Neo4j driver wrapper.

Owns a single `AsyncDriver` per process. Callers acquire it via
`get_driver()` and must call `close_driver()` at shutdown.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from neo4j import AsyncDriver, AsyncGraphDatabase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neo4jDriver:
    driver: AsyncDriver
    database: str = "neo4j"


_instance: Neo4jDriver | None = None


async def get_driver(uri: str, user: str, password: str, database: str = "neo4j") -> Neo4jDriver:
    """Return the process-wide driver, creating it on first call.

    Verifies connectivity once at creation — raises if the server is unreachable.
    """
    global _instance
    if _instance is not None:
        return _instance

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    await driver.verify_connectivity()
    logger.info("Neo4j driver connected to %s (db=%s)", uri, database)
    _instance = Neo4jDriver(driver=driver, database=database)
    return _instance


async def close_driver() -> None:
    global _instance
    if _instance is None:
        return
    await _instance.driver.close()
    _instance = None
    logger.info("Neo4j driver closed")
