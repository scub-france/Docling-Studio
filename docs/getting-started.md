# Getting Started

Docling Studio ships two Docker image variants:

| Variant | Image tag | Size | Description |
|---------|-----------|------|-------------|
| **remote** | `latest-remote` | ~270 MB | Lightweight — delegates to an external [Docling Serve](https://github.com/DS4SD/docling-serve) instance |
| **local** | `latest-local` | ~1.9 GB | Full — runs Docling in-process, CPU-only (downloads ML models on first run) |

![Docker architecture](images/docker.png){ width="600" }

## Docker — remote mode (fastest)

```bash
docker run -p 3000:3000 \
  -e DOCLING_SERVE_URL=http://your-docling-serve:5001 \
  ghcr.io/scub-france/docling-studio:latest-remote
```

## Docker — local mode (self-contained)

```bash
docker run -p 3000:3000 ghcr.io/scub-france/docling-studio:latest-local
```

> **Note:** The first analysis takes longer as Docling downloads its ML models (~400 MB). Subsequent runs are fast.

Open [http://localhost:3000](http://localhost:3000).

## Docker Compose (recommended for development)

```bash
git clone https://github.com/scub-france/Docling-Studio.git
cd Docling-Studio

# Local mode (default)
docker compose up --build

# Remote mode
CONVERSION_MODE=remote DOCLING_SERVE_URL=http://your-docling-serve:5001 docker compose up --build
```

## Local Development

=== "Backend (Python 3.12+)"

    ```bash
    cd document-parser
    python -m venv .venv && source .venv/bin/activate

    # Remote mode (lightweight)
    pip install -r requirements.txt

    # Local mode (with Docling)
    pip install -r requirements-local.txt

    uvicorn main:app --reload --port 8000
    ```

=== "Frontend (Node 20+)"

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

The frontend runs on `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

## Running Tests

=== "Backend"

    ```bash
    cd document-parser
    pip install pytest pytest-asyncio httpx
    pytest tests/ -v
    ```

=== "Frontend"

    ```bash
    cd frontend
    npm run test:run
    ```

## Pipeline Options

These options map directly to Docling's [`PdfPipelineOptions`](https://docling-project.github.io/docling/usage/).

| Option | Default | Description |
|--------|---------|-------------|
| `do_ocr` | `true` | OCR for scanned pages and embedded images |
| `do_table_structure` | `true` | Table detection and row/column reconstruction |
| `table_mode` | `accurate` | `accurate` (TableFormer) or `fast` |
| `do_code_enrichment` | `false` | Specialized OCR for code blocks |
| `do_formula_enrichment` | `false` | Math formula recognition (LaTeX output) |
| `do_picture_classification` | `false` | Classify images by type |
| `do_picture_description` | `false` | Generate image descriptions via VLM |
| `generate_picture_images` | `false` | Extract detected images as separate files |
| `generate_page_images` | `false` | Rasterize each page as an image |
| `images_scale` | `1.0` | Scale factor for generated images (0.1–10) |

## Chunking Options

!!! note
    Chunking is only available in **local** mode. The chunking UI is hidden when using remote mode (Docling Serve).

After a document is analyzed, you can split the extracted content into semantic chunks. Chunking can be configured at analysis time or re-run later with different options via the **rechunk** action.

| Option | Default | Description |
|--------|---------|-------------|
| `chunker_type` | `hybrid` | `hybrid` (semantic + structural), `hierarchical` (heading-based), or `page` (one chunk per page) |
| `max_tokens` | `512` | Maximum tokens per chunk |
| `merge_peers` | `true` | Merge sibling elements under the same heading |
| `repeat_table_header` | `true` | Repeat table headers when a table is split across chunks |

Each chunk includes:

- **text** — the chunk content
- **headings** — heading hierarchy leading to the chunk
- **source_page** — the page number the chunk originates from
- **token_count** — number of tokens in the chunk
- **bboxes** — bounding boxes of the chunk's source elements (page + coordinates)

## Configuration

All configuration is done via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CONVERSION_ENGINE` | `local` | `local` (in-process Docling) or `remote` (Docling Serve) |
| `DOCLING_SERVE_URL` | `http://localhost:5001` | Docling Serve endpoint (remote mode only) |
| `DOCLING_SERVE_API_KEY` | — | API key for Docling Serve (optional) |
| `CORS_ORIGINS` | `http://localhost:3000,...` | CORS allowed origins |
| `UPLOAD_DIR` | `./uploads` | File storage directory |
| `DB_PATH` | `./data/docling_studio.db` | SQLite database path |
| `CONVERSION_TIMEOUT` | `600` | Max seconds per Docling conversion |
| `MAX_CONCURRENT_ANALYSES` | `3` | Maximum parallel analysis jobs |
| `DEPLOYMENT_MODE` | `self-hosted` | `self-hosted` or `huggingface` (shows disclaimer banner) |
| `APP_VERSION` | `dev` | Application version (set automatically by CI/Docker) |

## System Requirements

| | Remote image | Local image |
|---|---|---|
| **Image size** | ~270 MB | ~1.9 GB |
| **Memory** | 2 GB | 6 GB (recommended 8 GB+) |
| **CPUs** | 2 | 4 (recommended 8+) |

All Docker images are multi-arch (`linux/amd64` + `linux/arm64`). No GPU required.
