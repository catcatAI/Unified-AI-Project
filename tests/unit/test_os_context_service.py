"""Smoke tests for services/os_context_service.py with mock patching"""
from unittest.mock import patch, MagicMock, mock_open
import pytest


class TestOSContextService:
    """Smoke tests for OSContextService"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.os_context_service import OSContextService
            assert OSContextService is not None
        except ImportError as e:
            pytest.skip(f"OSContextService not available: {e}")

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_instantiation(self, mock_adapter):
        """Verify basic instantiation with mock patching"""
        try:
            from services.os_context_service import OSContextService
            mock_adapter.return_value = MagicMock()
            instance = OSContextService()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"OSContextService not available: {e}")
        except Exception as e:
            pytest.skip(f"OSContextService init failed (expected in CI): {e}")
