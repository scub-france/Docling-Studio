# Neo4j integration — Docling-Studio v0.5.0

Design doc for Neo4j integration targeting release 0.5.0.
Target: Hackernoon hackathon demo (Neo4j partner).

---

## 1. Context and goals

### Already in Docling-Studio
- Ingestion pipeline: Docling parser → chunking (HybridChunker) → embedding → OpenSearch (vector index)
- Vue 3 + FastAPI UI
- Debug view to inspect/edit chunks before retrieval
- Docker compose with existing services

### What we add in v0.5.0
- Neo4j as **graph-native storage** of the document structure
- A new ingestion layer that stores the DoclingDocument tree faithfully as a graph
- Minimal UI to visualize the graph (demo value to the judges)
- Compose pipeline with Neo4j

### Why graph-native (hackathon positioning)
> Most document AI tools store parsed content as flat chunks in a vector DB.
> Docling-Studio v0.5 introduces a graph-native storage layer on top of Neo4j,
> preserving the full hierarchical structure of documents as first-class citizens.
> This unlocks hybrid retrieval, agentic navigation, and structural debugging —
> impossible with chunk-only stores.

### Out of scope for v0.5.0 (roadmap mention only)
- EnrichmentWriter (entities / summaries / keywords via docling-agent) — v0.6.0
- Agent reasoning trace viewer — v0.6.0
- RAG hybrid (graph traversal + vector) — v0.7.0
- Document versioning — v0.7.0+

---

## 2. Architectural principles

### Port & adapter, with nuance

**Write side**: one `Writer` port, **composable stages** (not alternative adapters).
Pipelines A and B are additive, not exclusive.

```
  CORE (always)          Pipeline A (RAG)       Pipeline B (agent-ready, v0.6+)
  ┌─────────────┐        ┌────────────────┐    ┌───────────────────┐
  │ TreeWriter  │ ─────▶ │ ChunkWriter    │    │ EnrichmentWriter  │
  │             │        │ (existing      │    │ (via docling-     │
  │             │        │  OpenSearch +  │    │  agent, v0.6+)    │
  │             │        │  adds chunks   │    │                   │
  │             │        │  to Neo4j)     │    │                   │
  └─────────────┘        └────────────────┘    └───────────────────┘
```

```python
# docling_studio/ingestion/pipeline.py
class Writer(Protocol):
    def write(self, doc: DoclingDocument, ctx: IngestionContext) -> None: ...

# Explicit composition per use case
def build_pipeline(config: PipelineConfig) -> list[Writer]:
    writers = [TreeWriter(neo4j_driver)]
    if config.rag_enabled:
        writers.append(ChunkWriter(neo4j_driver, chunker, embedder, opensearch))
    if config.enrichment_enabled:  # v0.6.0+
        writers.append(EnrichmentWriter(neo4j_driver, docling_agent))
    return writers
```

**Read side**: two distinct ports (same Neo4j backend, different queries).

```python
class RAGRetrievalPort(Protocol):
    def search(self, query: str, k: int) -> list[Chunk]: ...
    def similar(self, chunk_id: str, k: int) -> list[Chunk]: ...

class TreeNavigationPort(Protocol):  # v0.6.0+
    def get_outline(self, doc_id: str) -> Tree: ...
    def read_node(self, ref: str) -> Element: ...
    def list_children(self, ref: str) -> list[Element]: ...
    def walk(self, ref: str, depth: int) -> SubTree: ...
```

---

## 3. Neo4j schema

### Constraints & indexes (created at boot)

```cypher
// Uniqueness
CREATE CONSTRAINT document_id IF NOT EXISTS
  FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT element_composite IF NOT EXISTS
  FOR (e:Element) REQUIRE (e.doc_id, e.self_ref) IS UNIQUE;

CREATE CONSTRAINT page_composite IF NOT EXISTS
  FOR (p:Page) REQUIRE (p.doc_id, p.page_no) IS UNIQUE;

CREATE CONSTRAINT chunk_id IF NOT EXISTS
  FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

// Full-text index (element text search)
CREATE FULLTEXT INDEX element_text IF NOT EXISTS
  FOR (e:Element) ON EACH [e.text];

// Simple indexes for per-doc queries
CREATE INDEX element_doc IF NOT EXISTS FOR (e:Element) ON (e.doc_id);
CREATE INDEX chunk_doc  IF NOT EXISTS FOR (c:Chunk)   ON (c.doc_id);
```

### Data model

```cypher
// Root document
(:Document {
  id: string,                    // UUID or PDF hash
  title: string,
  source_uri: string,            // path or S3
  ingested_at: datetime,
  docling_version: string,
  stages_applied: list<string>,  // ["tree", "chunks"] etc.
  last_tree_write: datetime,
  last_chunk_write: datetime,
  tenant_id: string              // simple multi-tenancy
})

// All tree elements (shared :Element label + specific label)
(:Element:SectionHeader {doc_id, self_ref, text, level, prov_page, prov_bbox})
(:Element:Paragraph    {doc_id, self_ref, text, prov_page, prov_bbox})
(:Element:Table        {doc_id, self_ref, caption, cells_json, prov_page, prov_bbox})
(:Element:Figure       {doc_id, self_ref, caption, image_uri, prov_page, prov_bbox})
(:Element:ListItem     {doc_id, self_ref, text, marker, prov_page, prov_bbox})
(:Element:Formula      {doc_id, self_ref, latex, text, prov_page, prov_bbox})

// Page for layout provenance
(:Page {doc_id, page_no, width, height})

// Chunks (Pipeline A)
(:Chunk {
  id, doc_id,
  text,
  chunk_index,
  embedding_ref,   // id in OpenSearch (no inline duplication)
  token_count
})
```

### Relations

```cypher
// Hierarchical structure
(:Document)-[:HAS_ROOT]->(:Element)
(:Element)-[:PARENT_OF {order: int}]->(:Element)  // order preserves sequence
(:Element)-[:NEXT]->(:Element)                     // DFS pre-order reading

// Layout
(:Element)-[:ON_PAGE]->(:Page)

// Pipeline A (chunking)
(:Document)-[:HAS_CHUNK]->(:Chunk)
(:Chunk)-[:DERIVED_FROM]->(:Element)  // back-reference; a chunk can span multiple elements
```

### Decisions

| Decision | Choice | Rationale |
|----------|-------|---------------|
| Element composite key | `(doc_id, self_ref)` | self_ref not unique across docs |
| Multi-tenancy | `tenant_id` property on Document | Simple, filterable, migrable to multi-db later |
| Table cells | `cells_json` property | v0.5 KISS. May model `(Table)-[:HAS_CELL]->(Cell)` in v0.6+ |
| Reading order | `[:NEXT]` chain + `{order}` on `PARENT_OF` | Both views useful |
| Versioning | None (replace strategy on re-upload) | v0.5 KISS |
| APOC | Not required | Pure Cypher is sufficient for v0.5 |

### Re-ingestion strategy

```cypher
// Before ingesting, wipe existing
MATCH (d:Document {id: $doc_id})
OPTIONAL MATCH (d)-[:HAS_ROOT|HAS_CHUNK]->()
DETACH DELETE d
// Then re-walk cleanly
```

---

## 4. Implementation plan (3 days)

### Day 1 — Infra + schema

- [ ] Add `neo4j` service to `docker-compose.yml` (`neo4j:5.15-community`, persistent volume, healthcheck)
- [ ] Add env vars (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) to `.env.example`
- [ ] Create module `docling_studio/storage/neo4j/`:
  - `driver.py` — neo4j-python driver wrapper (connection pool, context manager)
  - `schema.py` — idempotent `bootstrap_schema()` (CREATE CONSTRAINT / INDEX at startup)
  - `__init__.py` with exports
- [ ] Hook `bootstrap_schema()` in FastAPI startup
- [ ] Basic integration tests:
  - Driver connection
  - Schema bootstrap (idempotence verified)
  - Simple round-trip: write Document, read Document, delete Document

**Deliverable:** docker compose boots with healthy Neo4j, schema in place at init.

### Day 2 — TreeWriter (write + read)

- [ ] `storage/neo4j/tree_writer.py` — `DoclingDocument → Neo4j` walker
  - `write_document(doc, tenant_id, driver)` in a transaction
  - DFS pre-order, batched `MERGE` for perf
  - Pages first, then Elements, then `PARENT_OF` / `NEXT` / `ON_PAGE` relations
  - Dynamic labels based on `node.label` (`SectionHeader`, `Paragraph`, …)
- [ ] `storage/neo4j/tree_reader.py` — inverse walker `Neo4j → DoclingDocument`
  - `read_document(doc_id, driver) -> DoclingDocument`
  - Loads all Elements + Pages, rebuilds the Pydantic structure
  - Prerequisite for v0.6 (feeding docling-agent from Neo4j)
- [ ] Integrate into existing ingestion pipeline:
  - Add TreeWriter as first stage of `IngestionPipeline`
  - `neo4j_enabled: bool` config toggle
- [ ] Round-trip tests:
  - 3–4 varied PDFs (academic, invoice, report)
  - Assertion: `doc_original == read_document(write_document(doc_original))`
  - Beware dates, bbox floats (tolerance)

**Deliverable:** A PDF uploaded to Docling-Studio is fully present in Neo4j and rebuildable.

### Day 3 — UI + ChunkWriter + packaging

- [ ] `storage/neo4j/chunk_writer.py`:
  - After existing chunking, push each Chunk to Neo4j
  - Create `(:Chunk)-[:DERIVED_FROM]->(:Element)` via source element `self_ref`
  - Do NOT duplicate embeddings (stay in OpenSearch, keep `embedding_ref`)
- [ ] Frontend: new "Graph view" tab in debug panel
  - Vue component with `cytoscape` (lighter, better layout API)
  - FastAPI endpoint `/api/documents/{doc_id}/graph` returns nodes + edges around a scope (whole doc or subtree)
  - View: vertical tree, colors per node type, click-to-zoom, hover details
- [ ] Per-document "Graph-ready" / "RAG-ready" badge in list
- [ ] README update:
  - "Graph storage with Neo4j" section
  - Schema diagram (Mermaid or image)
  - 2–3 Cypher examples like "find all paragraphs under section X that mention Y"
  - Neo4j badge in features list
- [ ] (bonus if time) "Query explorer" dev tab for live demo: Cypher editor + results

**Deliverable:** release 0.5.0 with Neo4j visible, functional, documented.

---

## 5. Proposed code structure

```
docling_studio/
├── storage/
│   ├── neo4j/
│   │   ├── __init__.py
│   │   ├── driver.py           # connection management
│   │   ├── schema.py           # bootstrap_schema()
│   │   ├── tree_writer.py      # DoclingDocument -> Neo4j
│   │   ├── tree_reader.py      # Neo4j -> DoclingDocument
│   │   ├── chunk_writer.py     # Chunks -> Neo4j
│   │   └── queries.py          # shared Cypher queries
│   ├── opensearch/             # (existing)
│   └── ports.py                # Writer, RAGRetrievalPort protocols
├── ingestion/
│   └── pipeline.py             # IngestionPipeline composing Writers
├── api/
│   └── graph.py                # /api/documents/{id}/graph
└── frontend/
    └── components/
        └── GraphView.vue       # cytoscape + graph API fetch
```

---

## 6. Docker compose (added excerpt)

```yaml
services:
  neo4j:
    image: neo4j:5.15-community
    environment:
      NEO4J_AUTH: ${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD:-changeme}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_server_memory_heap_initial__size: 512m
      NEO4J_server_memory_heap_max__size: 1g
    ports:
      - "7474:7474"   # Browser UI (demo)
      - "7687:7687"   # Bolt protocol
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p $${NEO4J_PASSWORD:-changeme} 'RETURN 1' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 10

  docling-studio-backend:
    depends_on:
      neo4j:
        condition: service_healthy
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD:-changeme}

volumes:
  neo4j_data:
  neo4j_logs:
```

---

## 7. Tests

### Unit tests
- `tests/storage/neo4j/test_schema.py` — bootstrap is idempotent
- `tests/storage/neo4j/test_tree_writer.py` — round-trip on synthetic DoclingDocument
- `tests/storage/neo4j/test_chunk_writer.py` — chunks written with correct `DERIVED_FROM`

### Integration tests
- `tests/integration/test_ingestion_pipeline.py` — full pipeline on a real PDF
- PDF fixtures: 1 academic (complex heading hierarchy), 1 invoice (tables), 1 report (lists)

### E2E (bonus)
- Upload PDF via UI → check structure in Neo4j Browser

---

## 8. Open decisions to settle before coding

1. **Neo4j edition**: Community (free) or AuraDB (managed) ?
   - Rec: Community in Docker for v0.5.0 dev/demo. AuraDB mentioned as prod option.

2. **Chunks: duplicate embeddings in Neo4j or OpenSearch ref ?**
   - Rec: OpenSearch ref (avoid duplication; OpenSearch remains source of truth for vectors). In v0.6+, consider native Neo4j vector index.

3. **Graph view UI: cytoscape or vis-network ?**
   - Rec: **cytoscape** — lighter, better layout API, used by Neo4j itself.

4. **Graph endpoint: return full doc or paginate ?**
   - Rec: full doc for v0.5 (reasonable cap at 200 pages). Pagination in v0.6.

5. **Error strategy**: if Neo4j is down at ingestion, fail or degrade gracefully ?
   - Rec: **fail fast** for v0.5 (avoid silent inconsistencies). `neo4j_required: bool` config option.

---

## 9. Hooks for later (v0.6.0+ — don't implement but prepare)

**EnrichmentWriter (v0.6)** — will need:
- The reader (Neo4j → DoclingDocument) to re-materialize the doc, feed docling-agent, re-patch enrichments
- A stage addable to `IngestionPipeline` without touching other stages
- An `:Entity` label (not created in v0.5 but schema-compatible)

**Agent reasoning trace viewer (v0.6)** — will need:
- An event stream (WebSocket) that v0.5 already prepares via the reactive UI
- A node_ref ↔ Element correlation in Neo4j (our composite `self_ref` key is enough)

**TreeNavigationPort (v0.7)** — will need:
- Optimized Cypher queries for descendant/ancestor walk (indexes already provisioned)

---

## 10. v0.5.0 success criteria

**Must have:**
- [ ] A PDF uploaded to Docling-Studio is in Neo4j with structure preserved
- [ ] Neo4j Browser shows the graph and is manually explorable
- [ ] A graph visual in the Docling-Studio UI works
- [ ] `docker compose up` works zero-config
- [ ] README mentions Neo4j and describes the schema

**Nice to have (decreasing priority):**
- [ ] Graph-ready / RAG-ready badge per doc
- [ ] Live query explorer in the UI
- [ ] 2–3 example queries in README that do something impossible with vector-only

**For the hackathon (post-release):**
- [ ] 60s video: upload PDF → structure in Neo4j → cross-doc query impossible in vector-only
- [ ] HackerNoon post explaining "graph-native documents" positioning
- [ ] Explicit Neo4j partnership mention

---

## 11. Fundamental architectural decisions recap

| Question | Answer |
|----------|---------|
| Is Neo4j source of truth or cache ? | **Source of truth** for structure. OpenSearch remains source of truth for embeddings. |
| Does chunking go away ? | No, v0.5.0 keeps existing chunking. "Chunkless" is Pipeline B, v0.6+. |
| Can it be toggled per doc ? | Yes — `stages_applied` on Document + pipeline config |
| What about OpenSearch ? | Stays, stores vectors. Neo4j tracks `(:Chunk)-[:DERIVED_FROM]->(:Element)` links. |
| Multi-tenancy ? | `tenant_id` property on Document, Cypher filter |
| Versioning ? | None for v0.5.0 — replace strategy on re-upload |

---

## Appendix — Demo queries

### Query 1 — All "Methods" sections across documents
```cypher
MATCH (d:Document)-[:HAS_ROOT]->(:Element)-[:PARENT_OF*]->(s:SectionHeader)
WHERE toLower(s.text) CONTAINS 'method'
RETURN d.title, s.text, s.level
```

### Query 2 — Context of a chunk (parent + siblings)
```cypher
MATCH (c:Chunk {id: $chunk_id})-[:DERIVED_FROM]->(e:Element)
MATCH (e)<-[:PARENT_OF]-(parent:Element)
MATCH (parent)-[:PARENT_OF]->(sibling:Element)
RETURN parent, collect(sibling) AS siblings
```

### Query 3 — All tables from a document type
```cypher
MATCH (d:Document)-[:HAS_ROOT]->(:Element)-[:PARENT_OF*]->(t:Table)
WHERE d.source_uri CONTAINS 'invoices/'
RETURN d.title, t.caption, t.cells_json
```

### Query 4 — Direct children of a section (ordered)
```cypher
MATCH (s:Element {doc_id: $doc_id, self_ref: $section_ref})
MATCH (s)-[pof:PARENT_OF]->(child)
RETURN child
ORDER BY pof.order
```

---

*Single reference doc for Neo4j v0.5.0 implementation.
Read this first in the implementation thread.*
