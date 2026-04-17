"""Neo4j storage adapter — graph-native document structure.

Provides a thin driver wrapper, idempotent schema bootstrap, and
walkers between DoclingDocument and the graph model.
"""

from infra.neo4j.driver import Neo4jDriver, close_driver, get_driver
from infra.neo4j.schema import bootstrap_schema

__all__ = ["Neo4jDriver", "bootstrap_schema", "close_driver", "get_driver"]
