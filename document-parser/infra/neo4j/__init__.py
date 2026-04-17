"""Neo4j storage adapter — graph-native document structure.

Provides a thin driver wrapper, idempotent schema bootstrap, and
walkers between DoclingDocument and the graph model.
"""

from infra.neo4j.driver import Neo4jDriver, close_driver, get_driver
from infra.neo4j.schema import bootstrap_schema
from infra.neo4j.tree_reader import (
    delete_document,
    document_exists,
    read_document_json,
)
from infra.neo4j.tree_writer import TreeWriteResult, write_document

__all__ = [
    "Neo4jDriver",
    "TreeWriteResult",
    "bootstrap_schema",
    "close_driver",
    "delete_document",
    "document_exists",
    "get_driver",
    "read_document_json",
    "write_document",
]
