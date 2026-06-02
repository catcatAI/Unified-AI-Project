"""Tests for services/os_context_service.py"""
from unittest.mock import patch, MagicMock
import pytest


class TestOSContextService:
    """Tests for OSContextService"""

    def test_import(self):
        from services.os_context_service import OSContextService
        assert OSContextService is not None

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_instantiation(self, mock_adapter):
        from services.os_context_service import OSContextService
        mock_adapter.return_value = MagicMock()
        instance = OSContextService()
        assert instance is not None
        assert instance.adapter is not None

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_get_current_state_for_ai_success(self, mock_adapter):
        from services.os_context_service import OSContextService
        mock_instance = MagicMock()
        mock_instance.get_summary.return_value = {
            "status": "success",
            "window_preview": [{"title": "Test"}],
            "clipboard_preview": "clip",
            "active_windows_count": 1,
        }
        mock_adapter.return_value = mock_instance
        svc = OSContextService()
        result = svc.get_current_state_for_ai()
        assert "active_windows" in result
        assert result["total_windows"] == 1

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_get_current_state_for_ai_failure(self, mock_adapter):
        from services.os_context_service import OSContextService
        mock_instance = MagicMock()
        mock_instance.get_summary.return_value = {"status": "error"}
        mock_adapter.return_value = mock_instance
        svc = OSContextService()
        result = svc.get_current_state_for_ai()
        assert "error" in result

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_perform_intelligent_action_click(self, mock_adapter):
        from services.os_context_service import OSContextService
        mock_instance = MagicMock()
        mock_instance.take_action.return_value = {"status": "success"}
        mock_adapter.return_value = mock_instance
        svc = OSContextService()
        result = svc.perform_intelligent_action("click button", "Submit")
        assert result is not None

    @patch('services.os_context_service.OSBridgeAdapter')
    def test_perform_intelligent_action_unsupported(self, mock_adapter):
        from services.os_context_service import OSContextService
        mock_adapter.return_value = MagicMock()
        svc = OSContextService()
        result = svc.perform_intelligent_action("unknown action")
        assert result["status"] == "unsupported_intent"
