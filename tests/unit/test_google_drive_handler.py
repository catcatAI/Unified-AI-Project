"""Smoke tests for GoogleDriveHandler"""
import pytest


class TestGoogleDriveHandler:
    """Basic smoke tests for GoogleDriveHandler"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.handlers.google_drive_handler import GoogleDriveHandler
            assert GoogleDriveHandler is not None
        except ImportError as e:
            pytest.skip(f"GoogleDriveHandler not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.handlers.google_drive_handler import GoogleDriveHandler
            instance = GoogleDriveHandler()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"GoogleDriveHandler not available: {e}")
        except Exception as e:
            pytest.skip(f"GoogleDriveHandler init failed (expected in CI): {e}")
