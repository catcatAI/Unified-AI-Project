"""Tests for GoogleDriveHandler"""
import pytest


class TestGoogleDriveHandler:
    """Tests for GoogleDriveHandler"""

    def test_import(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        assert GoogleDriveHandler is not None

    def test_instantiation(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        instance = GoogleDriveHandler()
        assert instance is not None
        assert instance._drive_service is None

    def test_handle_list_intent(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        import asyncio
        instance = GoogleDriveHandler()
        result = asyncio.run(instance.handle("列出文件", "google_drive"))
        assert result is not None
        assert isinstance(result, str)

    def test_handle_status_intent(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        import asyncio
        instance = GoogleDriveHandler()
        result = asyncio.run(instance.handle("狀態如何", "google_drive"))
        assert result is not None

    def test_handle_unknown_intent(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        import asyncio
        instance = GoogleDriveHandler()
        result = asyncio.run(instance.handle("做點別的", "google_drive"))
        assert result is not None
