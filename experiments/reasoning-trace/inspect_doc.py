#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "docling-agent",
#   "rich",
# ]
# ///
"""
Run a docling-agent RAG inspection on a Docling-Studio analysis job and dump the RAGResult.

Bypasses `DoclingRAGAgent.run()` (which discards the RAGResult) and calls the private
`_rag_loop()` directly so we can capture the per-iteration trace.

Loads the DoclingDocument from Studio's SQLite (`analysis_jobs.document_json`), so no
re-parsing of the PDF is needed — same doc the UI is showing.

Usage:
    uv run experiments/reasoning-trace/inspect_doc.py \\
        --job-id 722d5631-0089-44a3-a64a-7ce5b99579d3 \\
        --query "Quels sont les points clés de l'offre ?" \\
        --model granite4:micro-h

Output:
    experiments/reasoning-trace/output/<job-id-prefix>_<utc-timestamp>.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from docling_agent.agent.rag import DoclingRAGAgent
from docling_core.types.doc.document import DoclingDocument
from mellea.backends import model_ids as M
from mellea.backends.model_ids import ModelIdentifier

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DB_PATH = REPO / "document-parser" / "data" / "docling_studio.db"
OUT_DIR = HERE / "output"


def load_doc(job_id: str) -> tuple[DoclingDocument, str]:
    if not DB_PATH.exists():
        sys.exit(f"SQLite DB not found at {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        """
        SELECT aj.document_json, d.filename
        FROM analysis_jobs aj
        JOIN documents d ON d.id = aj.document_id
        WHERE aj.id = ?
        """,
        (job_id,),
    ).fetchone()
    con.close()
    if row is None:
        sys.exit(f"No analysis job with id {job_id}")
    if not row["document_json"]:
        sys.exit(f"Analysis job {job_id} has no document_json (not completed?)")
    return DoclingDocument.model_validate_json(row["document_json"]), row["filename"]


def resolve_model(name: str) -> ModelIdentifier:
    """Accept either a mellea catalog constant name (e.g. 'IBM_GRANITE_4_HYBRID_MICRO')
    or a raw Ollama tag (e.g. 'granite4:micro-h', 'llama3.2:3b')."""
    const = getattr(M, name.upper(), None)
    if isinstance(const, ModelIdentifier):
        return const
    return ModelIdentifier(ollama_name=name)


def summarize_structure(doc: DoclingDocument) -> str:
    from docling_core.types.doc.document import SectionHeaderItem, TitleItem

    headers = [
        item for item, _ in doc.iterate_items()
        if isinstance(item, (TitleItem, SectionHeaderItem))
    ]
    return (
        f"texts={len(doc.texts)} "
        f"tables={len(doc.tables)} "
        f"pictures={len(doc.pictures)} "
        f"groups={len(doc.groups)} "
        f"section_headers={len(headers)}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--job-id", required=True, help="analysis_jobs.id from Studio SQLite")
    p.add_argument("--query", required=True, help="Question to ask the document")
    p.add_argument(
        "--model",
        default="granite4:micro-h",
        help="Ollama tag or mellea catalog constant (default: granite4:micro-h)",
    )
    p.add_argument("--max-iters", type=int, default=5)
    p.add_argument("--quiet", action="store_true", help="disable rich progress panels")
    args = p.parse_args()

    print(f"→ Loading DoclingDocument from analysis {args.job_id[:8]}…")
    doc, filename = load_doc(args.job_id)
    print(f"  {filename}")
    print(f"  {summarize_structure(doc)}")

    model_id = resolve_model(args.model)
    print(f"→ Model: ollama={model_id.ollama_name!r} hf={model_id.hf_model_name!r}")

    agent = DoclingRAGAgent(
        model_id=model_id,
        tools=[],
        max_iterations=args.max_iters,
        verbose=not args.quiet,
    )

    print(f"→ Running RAG loop (query: {args.query!r})\n")
    # Intentional: agent.run() discards the RAGResult. _rag_loop gives us the trace.
    result = agent._rag_loop(query=args.query, doc=doc)

    OUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"{args.job_id[:8]}_{ts}.json"
    payload = {
        "job_id": args.job_id,
        "filename": filename,
        "query": args.query,
        "model": {
            "ollama_name": model_id.ollama_name,
            "hf_model_name": model_id.hf_model_name,
        },
        "max_iterations": args.max_iters,
        "result": json.loads(result.model_dump_json()),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print()
    print(f"✓ Wrote {out_path.relative_to(REPO)}")
    print(
        f"  converged={result.converged}  "
        f"iterations={len(result.iterations)}  "
        f"answer_chars={len(result.answer)}"
    )
    if result.iterations:
        print("  section_refs visited:", [it.section_ref for it in result.iterations])


if __name__ == "__main__":
    main()
