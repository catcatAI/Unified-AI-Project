"""Tests for GoogleDriveHandler — matches actual API"""
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
        assert instance.drive_service is None  # no underscore prefix

    def test_handle_with_params_dict(self):
        import asyncio

        from services.handlers.google_drive_handler import GoogleDriveHandler
        instance = GoogleDriveHandler()
        # handle() expects params as dict and returns dict, not string
        result = asyncio.run(instance.handle("google_drive_list", {"action": "list"}))
        assert result is not None
        assert isinstance(result, dict)

    def test_handle_default_returns_dict(self):
        import asyncio

        from services.handlers.google_drive_handler import GoogleDriveHandler
        instance = GoogleDriveHandler()
        result = asyncio.run(instance.handle("google_drive_status", {"action": "status"}))
        assert isinstance(result, dict)
        assert "status" in result
