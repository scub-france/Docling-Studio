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
    document_timeout: float = 120.0  # Docling-level per-document timeout (seconds)
    lock_timeout: int = 300  # converter lock acquisition timeout (seconds)
    max_concurrent_analyses: int = 3
    default_table_mode: str = "accurate"  # "accurate" or "fast"
    max_page_count: int = 0  # 0 = unlimited (upload validation)
    max_file_size: int = 0  # 0 = unlimited (Docling-level, bytes)
    max_file_size_mb: int = 50  # upload limit in MB (0 = unlimited)
    rate_limit_rpm: int = 100  # requests per minute per IP (0 = disabled)
    batch_page_size: int = 0  # 0 = disabled, > 0 = pages per batch
    opensearch_url: str = ""  # empty = disabled
    embedding_url: str = ""  # empty = disabled (e.g. http://localhost:8001)
    neo4j_uri: str = ""  # empty = disabled (e.g. bolt://neo4j:7687)
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    # Live reasoning via docling-agent — off by default (heavy deps, needs an
    # Ollama host reachable from the backend). Toggle RAG_ENABLED=true + point
    # OLLAMA_HOST at a running instance (default http://localhost:11434).
    rag_enabled: bool = False
    ollama_host: str = "http://localhost:11434"
    rag_model_id: str = "gpt-oss:20b"  # matches docling-agent's example_05
    opensearch_default_limit: int = 1000  # max chunks returned by get_chunks
    embedding_dimension: int = 384  # Granite Embedding 30M / all-MiniLM-L6-v2
    upload_dir: str = "./uploads"
    db_path: str = "./data/docling_studio.db"
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    def __post_init__(self) -> None:
        errors: list[str] = []
        if self.document_timeout <= 0:
            errors.append(f"document_timeout must be > 0 (got {self.document_timeout})")
        if self.conversion_timeout <= 0:
            errors.append(f"conversion_timeout must be > 0 (got {self.conversion_timeout})")
        if self.lock_timeout <= 0:
            errors.append(f"lock_timeout must be > 0 (got {self.lock_timeout})")
        if self.max_concurrent_analyses < 1:
            errors.append(
                f"max_concurrent_analyses must be >= 1 (got {self.max_concurrent_analyses})"
            )
        if self.max_page_count < 0:
            errors.append(f"max_page_count must be >= 0 (got {self.max_page_count})")
        if self.max_file_size < 0:
            errors.append(f"max_file_size must be >= 0 (got {self.max_file_size})")
        if self.max_file_size_mb < 0:
            errors.append(f"max_file_size_mb must be >= 0 (got {self.max_file_size_mb})")
        if self.rate_limit_rpm < 0:
            errors.append(f"rate_limit_rpm must be >= 0 (got {self.rate_limit_rpm})")
        if self.batch_page_size < 0:
            errors.append(f"batch_page_size must be >= 0 (got {self.batch_page_size})")
        if self.opensearch_default_limit < 1:
            errors.append(
                f"opensearch_default_limit must be >= 1 (got {self.opensearch_default_limit})"
            )
        if self.embedding_dimension < 1:
            errors.append(f"embedding_dimension must be >= 1 (got {self.embedding_dimension})")
        if self.default_table_mode not in ("accurate", "fast"):
            errors.append(
                f"default_table_mode must be 'accurate' or 'fast' (got '{self.default_table_mode}')"
            )
        # Timeout cascade: document_timeout < lock_timeout < conversion_timeout
        if self.document_timeout > 0 and self.lock_timeout > 0 and self.conversion_timeout > 0:
            if self.document_timeout >= self.lock_timeout:
                errors.append(
                    f"document_timeout ({self.document_timeout}s) must be "
                    f"< lock_timeout ({self.lock_timeout}s)"
                )
            if self.lock_timeout >= self.conversion_timeout:
                errors.append(
                    f"lock_timeout ({self.lock_timeout}s) must be "
                    f"< conversion_timeout ({self.conversion_timeout}s)"
                )
        if errors:
            raise ValueError("Invalid settings:\n  " + "\n  ".join(errors))

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
            document_timeout=float(os.environ.get("DOCUMENT_TIMEOUT", "120.0")),
            lock_timeout=int(os.environ.get("LOCK_TIMEOUT", "300")),
            max_concurrent_analyses=int(os.environ.get("MAX_CONCURRENT_ANALYSES", "3")),
            default_table_mode=os.environ.get("DEFAULT_TABLE_MODE", "accurate"),
            max_page_count=int(os.environ.get("MAX_PAGE_COUNT", "0")),
            max_file_size=int(os.environ.get("MAX_FILE_SIZE", "0")),
            max_file_size_mb=int(os.environ.get("MAX_FILE_SIZE_MB", "50")),
            rate_limit_rpm=int(os.environ.get("RATE_LIMIT_RPM", "100")),
            # 0 = batching disabled (matches dataclass default). Batching
            # preserves memory on very large docs but `merge_results` drops
            # `document_json`, which breaks the reasoning tunnel. Enable
            # explicitly (e.g. 50+) for memory-bound deploys.
            batch_page_size=int(os.environ.get("BATCH_PAGE_SIZE", "0")),
            opensearch_url=os.environ.get("OPENSEARCH_URL", ""),
            embedding_url=os.environ.get("EMBEDDING_URL", ""),
            neo4j_uri=os.environ.get("NEO4J_URI", ""),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", "changeme"),
            rag_enabled=os.environ.get("RAG_ENABLED", "false").lower()
            in ("1", "true", "yes", "on"),
            ollama_host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            rag_model_id=os.environ.get("RAG_MODEL_ID", "gpt-oss:20b"),
            opensearch_default_limit=int(os.environ.get("OPENSEARCH_DEFAULT_LIMIT", "1000")),
            embedding_dimension=int(os.environ.get("EMBEDDING_DIMENSION", "384")),
            upload_dir=os.environ.get("UPLOAD_DIR", "./uploads"),
            db_path=os.environ.get("DB_PATH", "./data/docling_studio.db"),
            cors_origins=[o.strip() for o in cors_raw.split(",")],
        )


# Module-level singleton — import this from other modules.
settings = Settings.from_env()
