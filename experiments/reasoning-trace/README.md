# Reasoning Trace — R&D sandbox

Goal: run `docling-agent`'s RAG loop against a document already ingested in
Docling-Studio, capture the `RAGResult` (per-iteration reasoning trace), and
inspect what the agent does.

Fully **isolated** from the Studio backend: no deps added to
`document-parser/`, no services modified. Just a script + uv inline deps.

---

## What it does

1. Reads the pre-parsed `DoclingDocument` directly from Studio's SQLite
   (`analysis_jobs.document_json`) — no PDF re-conversion.
2. Instantiates `DoclingRAGAgent` against a local Ollama model.
3. Calls `agent._rag_loop()` directly (the public `.run()` method discards the
   `RAGResult`; we need the iterations to see the reasoning trace).
4. Dumps the full `RAGResult` as JSON to `output/`.

---

## Prerequisites

### 1. Ollama running
```sh
# If not already running as a service:
ollama serve          # in another terminal
```

### 2. A model pulled
Recommended (Peter Staar's default, ~3B params, good JSON adherence):
```sh
ollama pull granite4:micro-h
```

Alternative already on your machine (2 GB, may struggle with strict JSON
rejection sampling):
```
llama3.2:3b
```

Bigger/more reliable but slower (20B):
```sh
ollama pull gpt-oss:20b
```

### 3. Pick an analysis job id
Any `COMPLETED` row from `analysis_jobs` with a non-null `document_json`:

```sh
sqlite3 document-parser/data/docling_studio.db \
  "SELECT aj.id, d.filename, length(aj.document_json)
   FROM analysis_jobs aj JOIN documents d ON d.id=aj.document_id
   WHERE aj.document_json IS NOT NULL AND aj.status='COMPLETED'
   ORDER BY length(aj.document_json) DESC LIMIT 5;"
```

On this machine, the biggest one right now is:
```
722d5631-0089-44a3-a64a-7ce5b99579d3  — CCI - Conférence IA - Offre Commerciale v1.0
```

---

## Run

```sh
uv run experiments/reasoning-trace/inspect_doc.py \
    --job-id 722d5631-0089-44a3-a64a-7ce5b99579d3 \
    --query "Quels sont les livrables principaux proposés ?" \
    --model granite4:micro-h
```

Flags:
- `--job-id` — required, analysis_jobs.id
- `--query` — required, the question
- `--model` — either a mellea catalog constant (`IBM_GRANITE_4_HYBRID_MICRO`)
  or a raw Ollama tag (`granite4:micro-h`, `llama3.2:3b`). Default:
  `granite4:micro-h`.
- `--max-iters` — default 5 (agent's own default)
- `--quiet` — disable the rich panels during the loop

First run will take ~1–2 min: `uv` solves the `docling-agent` env (pulls
docling-core, mellea, pydantic, rich, …) into a cached virtualenv. Subsequent
runs are instant.

---

## Output

`experiments/reasoning-trace/output/<job-id-prefix>_<utc>.json`

Schema:
```json
{
  "job_id": "…",
  "filename": "…",
  "query": "…",
  "model": { "ollama_name": "…", "hf_model_name": "…" },
  "max_iterations": 5,
  "result": {
    "answer": "…",
    "converged": true,
    "iterations": [
      { "iteration": 1, "section_ref": "#/texts/3",
        "reason": "…", "section_text_length": 412,
        "can_answer": false, "response": "…" },
      …
    ]
  }
}
```

This is the artifact the v1 Studio endpoint (`POST /api/rag/inspect`) will
import — so anything that works here should work there.

---

## Things to check on first run

- **Do we actually get a trace?** `iterations` list should have ≥ 1 entries
  (empty means "no section headers found" fallback — bad sign for the viz idea).
- **Are `section_ref` values `#/texts/N` paths or `#/groups/N`?** Determines
  how the resolver walks the tree.
- **Reasoning quality**: does `reason` actually explain the pick, or is it
  LLM filler? That affects whether the trace is worth surfacing visually.
- **Convergence rate**: with `max_iters=5`, does a small model converge at all,
  or hit the cap and return a partial answer?
- **Latency**: per-iteration wall-clock on your M-series machine with granite4.

---

## Next step (if the above looks promising)

Resolve each `iteration.section_ref` → `(page_no, bbox)` using the same
`DoclingDocument` that was loaded here. That's the `reasoning_service.py`
resolver described in `docs/design/reasoning-trace.md` §3.2 — implement it in
a second script here (`resolve_trace.py`) before touching Studio.
