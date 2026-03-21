# syntax=docker/dockerfile:1
# =============================================================================
# Docling Studio — single-image build (frontend + backend)
#
# Usage:
#   docker build -t docling-studio .
#   docker run -p 3000:3000 docling-studio
# =============================================================================

# --- Stage 1: Build frontend assets ---
FROM node:20-alpine AS frontend-build

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# --- Stage 2: Runtime (Python + Nginx) ---
FROM python:3.12-slim

# System deps: poppler (pdf2image), nginx, and OpenCV runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Python deps
WORKDIR /app
COPY document-parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY document-parser/ .

# Frontend static files
COPY --from=frontend-build /build/dist /usr/share/nginx/html

# Nginx config
COPY nginx.conf /etc/nginx/sites-enabled/default

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Data directories
RUN mkdir -p /app/uploads /app/data && chown -R appuser:appuser /app

ENV UPLOAD_DIR=/app/uploads
ENV DB_PATH=/app/data/docling_studio.db

EXPOSE 3000

# nginx needs to run as root for port binding, then drops to appuser for uvicorn
CMD ["sh", "-c", "nginx && exec su appuser -c 'uvicorn main:app --host 127.0.0.1 --port 8000'"]
