"""Minimal Document node round-trip — validates the driver + schema end-to-end."""

from __future__ import annotations

from infra.neo4j.schema import bootstrap_schema


async def test_document_write_read_delete(neo4j_driver):
    await bootstrap_schema(neo4j_driver)

    async with neo4j_driver.driver.session(database=neo4j_driver.database) as session:
        await session.run(
            "CREATE (d:Document {id: $id, title: $title, tenant_id: $tenant})",
            id="doc-42",
            title="Round-trip fixture",
            tenant="default",
        )

        result = await session.run(
            "MATCH (d:Document {id: $id}) RETURN d.title AS title, d.tenant_id AS tenant",
            id="doc-42",
        )
        record = await result.single()
        assert record is not None
        assert record["title"] == "Round-trip fixture"
        assert record["tenant"] == "default"

        await session.run("MATCH (d:Document {id: $id}) DETACH DELETE d", id="doc-42")
        gone = await (
            await session.run("MATCH (d:Document {id: $id}) RETURN d", id="doc-42")
        ).single()
        assert gone is None
