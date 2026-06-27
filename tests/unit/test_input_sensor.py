"""Tests for core.bio.input_sensor"""
from unittest.mock import MagicMock, patch

import pytest


class TestGlobalInputSensor:
    def test_import(self):
        from core.bio.input_sensor import GlobalInputSensor
        assert hasattr(GlobalInputSensor, 'start')
        assert hasattr(GlobalInputSensor, 'stop')
        assert hasattr(GlobalInputSensor, 'sniff_environment')
        assert hasattr(GlobalInputSensor, 'get_activity_metrics')

    @patch('integrations.os_bridge_adapter.OSBridgeAdapter')
    def test_instantiation(self, MockBridge):
        MockBridge.return_value = MagicMock()
        from core.bio.input_sensor import GlobalInputSensor
        instance = GlobalInputSensor()
        assert instance.activity_count == 0
        assert instance.running is False
        assert instance.active_category == "neutral"
        assert instance.active_window_title == ""

    @patch('integrations.os_bridge_adapter.OSBridgeAdapter')
    def test_category_map_keys(self, MockBridge):
        MockBridge.return_value = MagicMock()
        from core.bio.input_sensor import GlobalInputSensor
        instance = GlobalInputSensor()
        assert "gaming" in instance.category_map
        assert "coding" in instance.category_map
        assert "media" in instance.category_map
        assert "social" in instance.category_map
        assert "browsing" in instance.category_map
        for keywords in instance.category_map.values():
            assert len(keywords) > 0

    @patch('integrations.os_bridge_adapter.OSBridgeAdapter')
    def test_on_activity_increments_count(self, MockBridge):
        MockBridge.return_value = MagicMock()
        from core.bio.input_sensor import GlobalInputSensor
        instance = GlobalInputSensor()
        old_count = instance.activity_count
        instance._on_activity()
        assert instance.activity_count == old_count + 1

    @patch('integrations.os_bridge_adapter.OSBridgeAdapter')
    def test_get_activity_metrics_structure(self, MockBridge):
        MockBridge.return_value = MagicMock()
        from core.bio.input_sensor import GlobalInputSensor
        instance = GlobalInputSensor()
        metrics = instance.get_activity_metrics()
        assert "seconds_since_last_input" in metrics
        assert "input_density_bpm" in metrics
        assert "is_user_active" in metrics
        assert "active_category" in metrics
        assert "window_title" in metrics
        assert isinstance(metrics["is_user_active"], bool)
        assert metrics["active_category"] == "neutral"

    @patch('integrations.os_bridge_adapter.OSBridgeAdapter')
    def test_get_activity_metrics_user_active(self, MockBridge):
        MockBridge.return_value = MagicMock()
        from core.bio.input_sensor import GlobalInputSensor
        instance = GlobalInputSensor()
        instance._on_activity()
        metrics = instance.get_activity_metrics()
        assert metrics["is_user_active"] is True
        assert metrics["seconds_since_last_input"] < 1.0
