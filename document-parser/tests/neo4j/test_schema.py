"""Schema bootstrap is idempotent and produces the expected constraints/indexes."""

from __future__ import annotations

from infra.neo4j.schema import CONSTRAINTS, FULLTEXT_INDEXES, INDEXES, bootstrap_schema


async def _count_schema(neo4j_driver) -> tuple[int, int]:
    async with neo4j_driver.driver.session(database=neo4j_driver.database) as session:
        constraints = await (await session.run("SHOW CONSTRAINTS")).data()
        indexes = await (await session.run("SHOW INDEXES")).data()
    return len(constraints), len(indexes)


async def test_bootstrap_is_idempotent(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    first = await _count_schema(neo4j_driver)

    # Running a second time must not duplicate anything.
    await bootstrap_schema(neo4j_driver)
    second = await _count_schema(neo4j_driver)

    assert first == second
    # Sanity: we created at least what we declared.
    assert first[0] >= len(CONSTRAINTS)
    assert first[1] >= len(INDEXES) + len(FULLTEXT_INDEXES)


async def test_document_id_is_unique(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    async with neo4j_driver.driver.session(database=neo4j_driver.database) as session:
        await session.run("CREATE (d:Document {id: 'doc-1', title: 'first'})")
        with_err: Exception | None = None
        try:
            await session.run("CREATE (d:Document {id: 'doc-1', title: 'dup'})")
        except Exception as exc:
            with_err = exc
        assert with_err is not None, "unique constraint on Document.id must reject duplicates"
