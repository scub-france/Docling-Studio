# Docling Studio

A visual document analysis studio powered by [Docling](https://github.com/DS4SD/docling).

Upload a PDF, configure the extraction pipeline, and visualize the results — text, tables, images, formulas, bounding boxes — all from your browser.

![Docling Studio architecture](images/archi.png){ width="600" }

![Docling Studio — Execution Result](screenshots/DS-execution-result.png)

## Features

- **PDF viewer** with page navigation, bounding box overlay, and resizable results panel
- **Configurable Docling pipeline** — OCR, table extraction, code/formula enrichment, picture classification & description
- **Bounding box visualization** — color-coded element overlay directly on the PDF
- **Markdown & HTML export** of extracted content
- **Document management** — upload, list, delete
- **Analysis history** — re-visit and open past analyses
- **Dark / Light theme** and **FR / EN** localization

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Frontend** | Vue 3, TypeScript, Vite, Pinia |
| **Backend** | FastAPI, Docling 2.x, SQLite (aiosqlite) |
| **CI** | GitHub Actions (lint, type-check, test, build) |
| **Infra** | Docker Compose + Nginx |

## Quick Start

```bash
# Docker (fastest)
docker run -p 3000:3000 ghcr.io/scub-france/docling-studio:latest
```

Open [http://localhost:3000](http://localhost:3000) and upload a PDF.

!!! note
    The first analysis takes longer as Docling downloads its ML models (~400 MB). Subsequent runs are fast.

See [Getting Started](getting-started.md) for local development setup.

## License

[MIT](https://github.com/scub-france/Docling-Studio/blob/main/LICENSE) — Pier-Jean Malandrino
