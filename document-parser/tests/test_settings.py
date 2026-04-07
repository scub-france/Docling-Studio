"""Tests for Settings — environment variable parsing and defaults."""

from __future__ import annotations

from infra.settings import Settings


class TestSettingsDefaults:
    def test_default_values(self):
        s = Settings()
        assert s.app_version == "dev"
        assert s.conversion_engine == "local"
        assert s.deployment_mode == "self-hosted"
        assert s.docling_serve_url == "http://localhost:5001"
        assert s.docling_serve_api_key is None
        assert s.conversion_timeout == 600
        assert s.upload_dir == "./uploads"
        assert s.db_path == "./data/docling_studio.db"
        assert "http://localhost:3000" in s.cors_origins

    def test_frozen(self):
        """Settings should be immutable."""
        import pytest

        s = Settings()
        with pytest.raises(AttributeError):
            s.upload_dir = "/other"  # type: ignore[misc]


class TestSettingsFromEnv:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("APP_VERSION", "1.2.3")
        monkeypatch.setenv("CONVERSION_ENGINE", "remote")
        monkeypatch.setenv("DEPLOYMENT_MODE", "huggingface")
        monkeypatch.setenv("DOCLING_SERVE_URL", "http://serve:9000")
        monkeypatch.setenv("DOCLING_SERVE_API_KEY", "secret-key")
        monkeypatch.setenv("CONVERSION_TIMEOUT", "120")
        monkeypatch.setenv("UPLOAD_DIR", "/data/uploads")
        monkeypatch.setenv("DB_PATH", "/data/test.db")
        monkeypatch.setenv("CORS_ORIGINS", "http://a.com, http://b.com")

        s = Settings.from_env()

        assert s.app_version == "1.2.3"
        assert s.conversion_engine == "remote"
        assert s.deployment_mode == "huggingface"
        assert s.docling_serve_url == "http://serve:9000"
        assert s.docling_serve_api_key == "secret-key"
        assert s.conversion_timeout == 120
        assert s.upload_dir == "/data/uploads"
        assert s.db_path == "/data/test.db"
        assert s.cors_origins == ["http://a.com", "http://b.com"]

    def test_defaults_when_env_empty(self, monkeypatch):
        """When no env vars set, from_env returns sensible defaults."""
        for key in (
            "APP_VERSION",
            "CONVERSION_ENGINE",
            "DEPLOYMENT_MODE",
            "DOCLING_SERVE_URL",
            "DOCLING_SERVE_API_KEY",
            "CONVERSION_TIMEOUT",
            "UPLOAD_DIR",
            "DB_PATH",
            "CORS_ORIGINS",
        ):
            monkeypatch.delenv(key, raising=False)

        s = Settings.from_env()

        assert s.app_version == "dev"
        assert s.conversion_engine == "local"
        assert s.conversion_timeout == 600

    def test_cors_origins_split(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com,http://c.com")
        s = Settings.from_env()
        assert len(s.cors_origins) == 3
        assert s.cors_origins[2] == "http://c.com"
