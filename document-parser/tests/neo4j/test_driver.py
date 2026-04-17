"""Neo4j driver connectivity smoke test."""

from __future__ import annotations


async def test_driver_connects_and_runs_cypher(neo4j_driver):
    async with neo4j_driver.driver.session(database=neo4j_driver.database) as session:
        result = await session.run("RETURN 1 AS x")
        record = await result.single()
        assert record["x"] == 1
