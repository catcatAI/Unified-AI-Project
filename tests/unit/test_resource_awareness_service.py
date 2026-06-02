"""Tests for services/resource_awareness_service.py"""
from unittest.mock import patch, MagicMock
import pytest


class TestResourceAwarenessService:
    """Tests for ResourceAwarenessService"""

    def test_import(self):
        from services.resource_awareness_service import ResourceAwarenessService
        assert ResourceAwarenessService is not None

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_is_system_stressed(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.disk_usage.return_value.percent = 70.0
        instance = ResourceAwarenessService(config_filepath=None)
        assert instance.is_system_stressed() is False

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_is_system_stressed_high_cpu(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_percent.return_value = 90.0
        mock_psutil.virtual_memory.return_value.percent = 50.0
        mock_psutil.disk_usage.return_value.percent = 50.0
        instance = ResourceAwarenessService(config_filepath=None)
        assert instance.is_system_stressed() is True

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_throttling_factor_normal(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value.percent = 20.0
        mock_psutil.virtual_memory.return_value.available = 1024**3
        instance = ResourceAwarenessService(config_filepath=None)
        factor = instance.get_throttling_factor()
        assert 0.2 <= factor <= 1.0

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_throttling_factor_high_load(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_percent.return_value = 100.0
        mock_psutil.virtual_memory.return_value.percent = 100.0
        mock_psutil.virtual_memory.return_value.available = 1024**3
        instance = ResourceAwarenessService(config_filepath=None)
        factor = instance.get_throttling_factor()
        assert factor == pytest.approx(0.2, abs=0.1)

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_get_cpu_count(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value.percent = 0.0
        mock_psutil.virtual_memory.return_value.available = 1024**3
        mock_psutil.disk_usage.return_value.percent = 0.0
        instance = ResourceAwarenessService(config_filepath=None)
        assert instance.get_cpu_count() == 8

    @patch('services.resource_awareness_service.psutil')
    @patch('services.resource_awareness_service.yaml')
    def test_get_realtime_metrics(self, mock_yaml, mock_psutil):
        from services.resource_awareness_service import ResourceAwarenessService
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.virtual_memory.return_value.available = 2 * 1024**3
        mock_psutil.disk_usage.return_value.percent = 70.0
        instance = ResourceAwarenessService(config_filepath=None)
        metrics = instance.get_realtime_metrics()
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
        assert "is_stressed" in metrics
