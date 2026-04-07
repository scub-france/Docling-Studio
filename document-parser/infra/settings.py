"""Centralized application settings — loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    app_version: str = "dev"
    conversion_engine: str = "local"  # "local" or "remote"
    deployment_mode: str = "self-hosted"  # "self-hosted" or "huggingface"
    docling_serve_url: str = "http://localhost:5001"
    docling_serve_api_key: str | None = None
    conversion_timeout: int = 900
    max_concurrent_analyses: int = 3
    max_page_count: int = 0  # 0 = unlimited
    upload_dir: str = "./uploads"
    db_path: str = "./data/docling_studio.db"
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    @classmethod
    def from_env(cls) -> Settings:
        """Build a Settings instance from environment variables."""
        cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        return cls(
            app_version=os.environ.get("APP_VERSION", "dev"),
            conversion_engine=os.environ.get("CONVERSION_ENGINE", "local"),
            deployment_mode=os.environ.get("DEPLOYMENT_MODE", "self-hosted"),
            docling_serve_url=os.environ.get("DOCLING_SERVE_URL", "http://localhost:5001"),
            docling_serve_api_key=os.environ.get("DOCLING_SERVE_API_KEY"),
            conversion_timeout=int(os.environ.get("CONVERSION_TIMEOUT", "900")),
            max_concurrent_analyses=int(os.environ.get("MAX_CONCURRENT_ANALYSES", "3")),
            max_page_count=int(os.environ.get("MAX_PAGE_COUNT", "0")),
            upload_dir=os.environ.get("UPLOAD_DIR", "./uploads"),
            db_path=os.environ.get("DB_PATH", "./data/docling_studio.db"),
            cors_origins=[o.strip() for o in cors_raw.split(",")],
        )


# Module-level singleton — import this from other modules.
settings = Settings.from_env()
