# Reasoning Trace Viewer — Docling-Studio v0.6.0 (R&D preview)

Design doc for the `docling-agent` reasoning trace viewer.
Targeted release: **v0.6.0** (R&D branched from `release/0.5.0` in parallel to the
0.5 build, so the Neo4j foundation can be leveraged without blocking the hackathon deliverable).

Positioning one-liner:
> Studio becomes the **reference viewer for any `docling-agent` run** — not another
> chatbot. The PDF is the debug surface.

---

## 1. Context

### Upstream trigger
Peter Staar (IBM) suggested surfacing the LLM reasoning trace as `docling-agent`
walks a `DoclingDocument` outline (chunkless RAG, new IBM repo).

### `docling-agent` in one paragraph
`DoclingRAGAgent(model_id, tools, max_iterations=5).run(task, sources=[doc])` returns
a `RAGResult` with `answer`, `converged`, and `iterations: list[RAGIteration]`.
Each `RAGIteration` carries: `iteration`, `section_ref` (JSON-pointer, e.g. `#/texts/3`),
`reason`, `can_answer`, `response`, `section_text_length`. No bbox — must be resolved
through `DoclingDocument.<items>[i].prov[0].bbox` + `page_no`. Runs on Mellea
(Ollama / OpenAI / HF / WatsonX / LiteLLM / Bedrock). Observability is stdout logs only.

### What Studio already brings
- **Neo4j graph of the document** (0.5.0, just landed) — every `Element` is keyed by
  `(doc_id, self_ref)`, Cytoscape node id is `elem::${self_ref}`. **This is the
  killer enabler.** `RAGIteration.section_ref → node` is a string concat, no resolver.
- `GraphView.vue` (Cytoscape + dagre) already handles styles via selectors
  (`selector: 'edge[type = "NEXT"]'`, `selector: 'node[kind = "section"]'`) — adding
  a `visited` class + `REASONING_NEXT` synthetic edge type is ~20 LOC of style.
- `analysis_jobs.document_json` in SQLite → DoclingDocument available for the sidecar
  runner (no PDF re-conversion). Not used by the viewer itself.

### Personas
- **v1 (this plan)**: dev / integrator of `docling-agent` debugging a run that went wrong.
- **v2 (roadmap)**: live runner with synchronized demo UX.
- v3+ (non-goals here): business analyst for semantic navigation, batch QA.

---

## 2. Scope split — **debug first, demo second**

Rendering surface pivoted: **the trace is drawn on the Neo4j graph**, not on the PDF.
See §1. This kills the whole bbox-resolution stack from v1.

| Phase | Value | Runtime deps | Surface |
|---|---|---|---|
| **v1 — Debug (this plan)** | Import externally-produced `RAGResult` JSON, overlay trace on the existing GraphView | **None** server-side. Pure frontend. | GraphView: visited nodes highlighted in order, synthetic `REASONING_NEXT` edges |
| **v2 — Demo (follow-up)** | Run the agent live against a loaded document | Ollama + Mellea + `docling-agent` (new opt-dep group `rag`) | Same GraphView + SSE streaming of iterations, staggered reveal |

Building v1 first de-risks the **graph-trace UX** on real runs (produced by the
R&D sidecar — see `experiments/reasoning-trace/`) before wiring the live runner.
Code shared between v1 and v2 is the GraphView overlay itself — 100 % reused.

**Prerequisite for v1**: the target document must have been processed through the
"Maintain" step (Neo4j pipeline). Otherwise the graph is empty and the trace has
nowhere to render — surface an explicit "Run the Maintain step first" empty state.

---

## 3. v1 — Debug mode (frontend-only)

### 3.1 No backend changes in v1

The GraphView already loads nodes keyed by `self_ref` via `GET /api/documents/{doc_id}/graph`.
Iteration `section_ref` → Cytoscape node id is `` `elem::${section_ref}` `` — a client-side
string concat. Nothing to compute server-side.

Consequences:
- No new router, no new service, no new pydantic model, no new migration.
- No dependency on `docling-agent` in `document-parser/requirements.txt`.
- `RAGResult` JSON (as produced by `experiments/reasoning-trace/`) is consumed
  entirely by the frontend.

### 3.2 Frontend — feature folder

New `frontend/src/features/reasoning/`:

```
reasoning/
├── store/reasoningStore.ts         # Pinia: trace, activeIteration, importDialogOpen
├── ui/
│   ├── ReasoningPanel.vue          # Side panel: query, answer, iteration list
│   ├── IterationCard.vue           # Single iteration row (reason + can_answer badge)
│   ├── ImportTraceDialog.vue       # Drag-drop / paste RAGResult JSON
│   └── GraphReasoningOverlay.ts    # NOT a component — a plugin that decorates cy
└── types.ts                        # RAGIteration, RAGResult mirror types
```

### 3.3 Graph overlay — how it's drawn

`GraphReasoningOverlay` takes the existing `cy` Cytoscape instance (exposed from
`GraphView.vue` via `defineExpose`) and:

1. For each `iteration[i].section_ref`, find node `` `elem::${section_ref}` ``. If
   missing, tag as `resolution_status: "not_in_graph"` and show a warning in the panel
   (common cause: doc not processed through Maintain, or agent returned a ref that
   points at a non-Element node).
2. Add class `visited` + data attribute `visitOrder: i+1` on matched nodes.
3. Insert **synthetic edges** between successive visited nodes with `type: "REASONING_NEXT"`
   and `data: { order: i }`. These edges are UI-only, never written to Neo4j.
4. On import, fit viewport to the visited subgraph (`cy.fit(cy.$('.visited'), 80)`).
5. On iteration card click → `cy.$(`#elem::${ref}`).flashClass('pulse', 800)` +
   centered pan.

Cytoscape styles (append to the existing stylesheet array in `GraphView.vue`):

```js
{ selector: 'node.visited',
  style: { 'border-color': '#EA580C', 'border-width': 3, 'overlay-opacity': 0 } },
{ selector: 'node.visited[visitOrder]',
  style: { label: 'data(visitOrder)', 'text-valign': 'top',
           'text-background-color': '#EA580C', 'text-background-opacity': 1,
           'color': '#FFFFFF', 'font-weight': 700 } },
{ selector: 'edge[type = "REASONING_NEXT"]',
  style: { 'line-color': '#EA580C', 'target-arrow-color': '#EA580C',
           'target-arrow-shape': 'triangle', 'curve-style': 'bezier',
           width: 2, 'z-index': 99 } },
```

Color ramp: single warm color (`#EA580C`) for v1. Gradient cold→warm is v2 polish.

### 3.4 Integration points

- `StudioPage.vue` → "Maintain" tab gains an **"Import reasoning trace"** action
  (don't add a 3rd mode — the viz lives inside the graph view, not a new workspace).
- `GraphView.vue` → add `defineExpose({ cy })` + a `<slot name="overlay" :cy="cy"/>`
  that the parent can populate with `<ReasoningPanel>`.
- `ReasoningPanel` appears as a right rail when a trace is loaded; collapsible.

### 3.5 Empty / error states

- **Graph empty for this doc** → "Run the Maintain step first. Neo4j has no graph for
  this document yet." (the Maintain button is literally next to it.)
- **All `section_ref`s unresolved in graph** → "None of the visited sections exist in
  the graph. The agent may have been run against a different document, or the doc was
  re-analyzed since. Re-run Maintain or re-run the agent."
- **Some resolved, some not** → show trace with the missing ones greyed out in the panel.

### 3.6 Tests

No backend tests in v1 (no backend code).

Frontend (Vitest):
- `reasoningStore.test.ts` — import trace, active iteration transitions, reset on doc change.
- `graphReasoningOverlay.test.ts` — given a mock `cy` (`cytoscape({ headless: true })`)
  with a known node set, verify `visited` class applied to the right ids and the
  correct synthetic edges added.
- `ReasoningPanel.test.ts` — empty / loaded / partial-resolution states.

### 3.7 Out of scope for v1
- Live agent runner (v2).
- Multi-doc queries — reject import if `RAGResult` was produced against `len(sources) > 1`.
- Phrase-level attribution — `docling-agent` doesn't emit it.
- Persisting traces in Neo4j — see §7.
- PDF highlighting — dropped from v1. Could come back as v2.5 if demand exists.

---

## 4. File inventory (v1)

**New — R&D sidecar** (already scaffolded on this branch)
- `experiments/reasoning-trace/inspect_doc.py` — self-contained `uv run` script.
- `experiments/reasoning-trace/README.md`
- `experiments/reasoning-trace/.gitignore`

**New — frontend**
- `frontend/src/features/reasoning/**` (see §3.2)
- Vitest siblings under `**/*.test.ts`

**Touched**
- `frontend/src/features/analysis/ui/GraphView.vue` — `defineExpose({ cy })` +
  `<slot name="overlay">` + 3 new style selectors.
- `frontend/src/pages/StudioPage.vue` — "Import reasoning trace" action in the
  Maintain tab rail.

**Untouched**
- Entire `document-parser/` backend — no new router, service, schema, or dep.
- `pyproject.toml` / `requirements.txt` — **no new runtime dep in v1**.
- Neo4j schema — synthetic edges are client-side Cytoscape only.
- OpenSearch / ingestion — untouched.
- SQLite schema — no migration.

---

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| `RAGResult` schema drifts in `docling-agent` | `schema_version` discriminator; strict pydantic; one canonical fixture from Peter pinned in CI. |
| `section_ref` variants (`#/texts/3` vs `#/body/texts/3`) | Normalize in parser; regex test matrix. |
| Synthetic groups without `prov` | Documented child-walk fallback + `resolved_via_child` status surfaced in UI. |
| Large `RAGResult` (hundreds of iterations) | Hard-cap `iterations` at 50 in v1 (Peter's agent uses `max_iterations=5` by default) — return 413 above. |
| `document_json` blob large (some docs > 5 MB) | `analysis_repo` already handles it; but **do not** log the blob. Add redaction test. |
| Section ref not in graph (doc not through Maintain, or re-analyzed) | Explicit empty-state in `ReasoningPanel` with a link to the Maintain tab. Partial resolution shown as grey in the trace list. |
| Feature creeping into 0.5.0 | This branch targets **v0.6.0**. Do not merge into `release/0.5.0`. Rebase onto the next release branch when cut. |

---

## 6. Spec anchoring

Pin the `RAGResult` shape to **docling-agent commit SHA at the time of v1 merge** in
a short ADR `docs/architecture/adrs/ADR-002-rag-result-schema.md`. The schema is
upstream, unversioned, and will move — this doc freezes the contract Studio imports.

---

## 7. v2 preview — demo mode (not in this plan)

Kept here to constrain v1 interfaces so nothing needs rewriting:
- `POST /api/rag/answer` — server-side runner. Accepts `{doc_id, question, model_id}`.
  Streams iterations via SSE. Frontend consumes the stream with the same
  `GraphReasoningOverlay` used by v1 import — iterations appear one by one with
  staggered reveal (~400 ms) as the SSE stream drips them in.
- Ollama wired through `Mellea` — new optional dep group `rag`.
- Persist traces in Neo4j as `(:ReasoningRun {id, query, converged})-[:VISITED {order,
  reason, can_answer}]->(:Element)` for replay + cross-run analytics. Leverages
  `TreeWriter` pattern already present. This is where the synthetic UI edges become
  real graph edges.
- Cross-run comparison view: overlay multiple runs on the same graph, diff the paths.

---

## 8. Branch & workflow

- Branch: **`feature/reasoning-trace`** off `origin/release/0.5.0`.
- Merge target: **next release branch (`release/0.6.0`)** once cut — *not* `0.5.0`.
- Until then: live on the feature branch; rebase onto `release/0.5.0` periodically to
  absorb Neo4j fixes.
- Issues: one umbrella + one per §4 subsystem (resolver, endpoint, UI panel, overlay,
  import dialog, tests). Commit with `Closes #NNN` per project convention.
- PR: opened against `release/0.6.0` when available; draft in the meantime.

---

## 9. Open questions (answered by the sidecar first run)

1. Are emitted `section_ref`s reachable as `elem::${ref}` in the Neo4j graph built
   by `TreeWriter`? I.e. is the `self_ref` the agent sees the same `self_ref` we
   wrote to the graph? (Expected yes — both come from the same `DoclingDocument` —
   but the sidecar on a real doc from SQLite will confirm in one run.)
2. Hit rate of the agent: with `max_iterations=5` and `granite4:micro-h`, does it
   converge, and how many sections does it actually visit? Determines if the overlay
   ever has more than 1–2 marked nodes (and whether `REASONING_NEXT` edges are worth
   the effort vs just node markers).
3. Quality of `iteration.reason` — is it substantive enough to show in the panel, or
   LLM filler we should hide? Sidecar output will tell.
4. Fallback when no section headers exist (`RAGResult(iterations=[], converged=True,
   answer=<full md>)` — see rag.py): what does the panel show? Probably a degraded
   "no trace available, full-doc answer" state.
