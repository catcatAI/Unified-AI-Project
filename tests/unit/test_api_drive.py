"""Tests for api/v1/endpoints/drive.py"""
import pytest


class TestDriveDeduplication:
    """Tests for DriveDeduplication"""

    def test_import(self):
        from api.v1.endpoints.drive import DriveDeduplication
        assert DriveDeduplication is not None

    def test_import_router(self):
        from api.v1.endpoints.drive import router
        assert router is not None
        assert router.prefix == "/drive"

    def test_should_download_new_file(self):
        from api.v1.endpoints.drive import DriveDeduplication
        instance = DriveDeduplication()
        assert instance.should_download({"id": "new_id", "content_hash": "abc"}) is True

    def test_should_download_no_id(self):
        from api.v1.endpoints.drive import DriveDeduplication
        instance = DriveDeduplication()
        assert instance.should_download({"content_hash": "abc"}) is True

    def test_record_sync_and_should_download_skip(self):
        from api.v1.endpoints.drive import DriveDeduplication
        instance = DriveDeduplication()
        instance.record_sync({"id": "doc1", "name": "test"}, "hash1")
        assert instance.should_download({"id": "doc1", "content_hash": "hash1"}) is False

    def test_record_sync_and_should_download_changed(self):
        from api.v1.endpoints.drive import DriveDeduplication
        instance = DriveDeduplication()
        instance.record_sync({"id": "doc1", "name": "test"}, "hash1")
        assert instance.should_download({"id": "doc1", "content_hash": "hash2"}) is True

    def test_compute_content_hash_missing_file(self):
        from api.v1.endpoints.drive import DriveDeduplication
        instance = DriveDeduplication()
        h = instance.compute_content_hash("/nonexistent/file.txt")
        assert h == ""


class TestDocumentParser:
    """Tests for DocumentParser"""

    def test_import(self):
        from api.v1.endpoints.drive import DocumentParser
        assert DocumentParser is not None

    def test_parse_nonexistent_file(self):
        from api.v1.endpoints.drive import DocumentParser
        parser = DocumentParser()
        result = parser.parse_document("/nonexistent/file.txt")
        assert result == ""

    def test_parse_unknown_suffix(self):
        from api.v1.endpoints.drive import DocumentParser
        parser = DocumentParser()
        result = parser.parse_document("file.xyz")
        assert "[File:" in result
        assert "xyz" in result
