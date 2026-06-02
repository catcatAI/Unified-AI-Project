"""Tests for integrations/google_drive_service.py"""
import pytest


class TestGoogleDriveService:
    """Tests for GoogleDriveService"""

    def test_import(self):
        from integrations.google_drive_service import GoogleDriveService
        assert GoogleDriveService is not None

    def test_import_router(self):
        from api.v1.endpoints.drive import router
        assert router is not None
