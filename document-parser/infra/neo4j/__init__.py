"""Neo4j storage adapter — graph-native document structure.

Provides a thin driver wrapper, idempotent schema bootstrap, and
walkers between DoclingDocument and the graph model.
"""

from infra.neo4j.chunk_writer import ChunkWriteResult, write_chunks
from infra.neo4j.driver import Neo4jDriver, close_driver, get_driver
from infra.neo4j.queries import fetch_graph
from infra.neo4j.schema import bootstrap_schema
from infra.neo4j.tree_reader import (
    delete_document,
    document_exists,
    read_document_json,
)
from infra.neo4j.tree_writer import TreeWriteResult, write_document

__all__ = [
    "ChunkWriteResult",
    "Neo4jDriver",
    "TreeWriteResult",
    "bootstrap_schema",
    "close_driver",
    "delete_document",
    "document_exists",
    "fetch_graph",
    "get_driver",
    "read_document_json",
    "write_chunks",
    "write_document",
]
