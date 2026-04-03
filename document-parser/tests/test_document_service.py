"""Tests for document_service — upload, preview, page counting, and deletion."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.models import Document
from services import document_service


class TestUploadValidation:
    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        content = b"x" * (document_service.MAX_FILE_SIZE + 1)
        with pytest.raises(ValueError, match="File too large"):
            await document_service.upload("big.pdf", "application/pdf", content)

    @pytest.mark.asyncio
    async def test_rejects_non_pdf(self):
        content = b"NOT-A-PDF-FILE"
        with pytest.raises(ValueError, match="not a PDF"):
            await document_service.upload("fake.pdf", "application/pdf", content)

    @pytest.mark.asyncio
    async def test_accepts_valid_pdf(self, tmp_path, monkeypatch):
        monkeypatch.setattr(document_service, "UPLOAD_DIR", str(tmp_path))

        mock_insert = AsyncMock()
        with (
            patch("persistence.document_repo.insert", mock_insert),
            patch.object(document_service, "_count_pages", return_value=5),
        ):
            content = b"%PDF-1.4 fake pdf content"
            doc = await document_service.upload("test.pdf", "application/pdf", content)

        assert doc.filename == "test.pdf"
        assert doc.file_size == len(content)
        assert doc.page_count == 5
        mock_insert.assert_called_once()

        # Verify file was actually written to disk
        assert os.path.exists(doc.storage_path)
        with open(doc.storage_path, "rb") as f:
            assert f.read() == content


class TestGeneratePreview:
    def test_raises_on_invalid_page(self):
        """generate_preview should raise ValueError when page is out of range."""
        with (
            patch("services.document_service.convert_from_bytes", return_value=[]),
            pytest.raises(ValueError, match="Page 1 not found"),
        ):
            document_service.generate_preview(b"%PDF-fake", page=1)

    def test_returns_png_bytes(self):
        """generate_preview should return PNG bytes from pdf2image."""
        mock_image = MagicMock()
        mock_image.save = MagicMock(side_effect=lambda buf, format: buf.write(b"PNG-DATA"))

        with patch("services.document_service.convert_from_bytes", return_value=[mock_image]):
            result = document_service.generate_preview(b"%PDF-fake", page=1, dpi=72)

        assert result == b"PNG-DATA"


class TestCountPages:
    def test_returns_page_count(self):
        with patch(
            "services.document_service.pdfinfo_from_bytes",
            return_value={"Pages": 42},
        ):
            assert document_service._count_pages(b"pdf") == 42

    def test_returns_none_on_error(self):
        with patch(
            "services.document_service.pdfinfo_from_bytes",
            side_effect=FileNotFoundError("poppler not found"),
        ):
            assert document_service._count_pages(b"pdf") is None


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_file_and_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr(document_service, "UPLOAD_DIR", str(tmp_path))

        # Create a fake file
        fake_file = tmp_path / "test.pdf"
        fake_file.write_bytes(b"content")

        doc = Document(
            id="doc-1",
            filename="test.pdf",
            storage_path=str(fake_file),
        )

        with (
            patch("persistence.document_repo.find_by_id", AsyncMock(return_value=doc)),
            patch("persistence.analysis_repo.delete_by_document", AsyncMock(return_value=2)),
            patch("persistence.document_repo.delete", AsyncMock(return_value=True)),
        ):
            result = await document_service.delete("doc-1")

        assert result is True
        assert not fake_file.exists()

    @pytest.mark.asyncio
    async def test_delete_refuses_file_outside_upload_dir(self, tmp_path, monkeypatch):
        """Files outside UPLOAD_DIR should not be deleted (path traversal protection)."""
        monkeypatch.setattr(document_service, "UPLOAD_DIR", str(tmp_path / "uploads"))
        os.makedirs(tmp_path / "uploads", exist_ok=True)

        # File is outside the upload dir
        outside_file = tmp_path / "secret.txt"
        outside_file.write_bytes(b"secret")

        doc = Document(id="doc-1", filename="x.pdf", storage_path=str(outside_file))

        with (
            patch("persistence.document_repo.find_by_id", AsyncMock(return_value=doc)),
            patch("persistence.analysis_repo.delete_by_document", AsyncMock(return_value=0)),
            patch("persistence.document_repo.delete", AsyncMock(return_value=True)),
        ):
            await document_service.delete("doc-1")

        # File should NOT have been deleted
        assert outside_file.exists()

    @pytest.mark.asyncio
    async def test_delete_not_found_returns_false(self):
        with patch("persistence.document_repo.find_by_id", AsyncMock(return_value=None)):
            result = await document_service.delete("missing")
        assert result is False
