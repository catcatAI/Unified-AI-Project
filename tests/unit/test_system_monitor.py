"""Tests for monitoring/system_monitor.py"""
from unittest.mock import MagicMock, patch

import pytest


class TestSystemMonitor:
    """Tests for SystemMonitor"""

    def test_import(self):
        from monitoring.system_monitor import SystemMonitor
        assert SystemMonitor is not None

    @patch('monitoring.system_monitor.psutil')
    @patch('monitoring.system_monitor.pynvml')
    def test_instantiation(self, mock_pynvml, mock_psutil):
        from monitoring.system_monitor import SystemMonitor
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 ** 3
        mock_psutil.disk_usage.return_value.used = 50
        mock_psutil.disk_usage.return_value.total = 100
        mock_psutil.disk_usage.return_value.percent = 50.0
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=2000)
        mock_pynvml.nvmlInit.side_effect = ImportError
        instance = SystemMonitor(config={})
        assert instance is not None
        assert instance.gpu_available is False

    @patch('monitoring.system_monitor.psutil')
    @patch('monitoring.system_monitor.pynvml')
    def test_collect_metrics(self, mock_pynvml, mock_psutil):
        from monitoring.system_monitor import SystemMonitor
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 ** 3
        mock_psutil.disk_usage.return_value.used = 50
        mock_psutil.disk_usage.return_value.total = 100
        mock_psutil.disk_usage.return_value.percent = 50.0
        mock_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.net_io_counters.return_value = mock_net
        mock_pynvml.nvmlInit.side_effect = ImportError
        instance = SystemMonitor(config={})
        metrics = instance.collect_metrics()
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_usage_percent == 50.0

    @patch('monitoring.system_monitor.psutil')
    @patch('monitoring.system_monitor.pynvml')
    def test_get_current_load(self, mock_pynvml, mock_psutil):
        from monitoring.system_monitor import SystemMonitor
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value.percent = 40.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 ** 3
        mock_psutil.disk_usage.return_value.used = 50
        mock_psutil.disk_usage.return_value.total = 100
        mock_psutil.disk_usage.return_value.percent = 50.0
        mock_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.net_io_counters.return_value = mock_net
        mock_pynvml.nvmlInit.side_effect = ImportError
        instance = SystemMonitor(config={})
        # collect first to populate history
        instance.collect_metrics()
        load = instance.get_current_load()
        assert "cpu_load" in load
        assert "memory_load" in load
        assert "disk_load" in load
        assert "network_bandwidth_usage" in load
        assert "gpu_load" in load

    @patch('monitoring.system_monitor.psutil')
    @patch('monitoring.system_monitor.pynvml')
    def test_get_resource_recommendations_no_history(self, mock_pynvml, mock_psutil):
        from monitoring.system_monitor import SystemMonitor
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 ** 3
        mock_psutil.disk_usage.return_value.used = 50
        mock_psutil.disk_usage.return_value.total = 100
        mock_psutil.disk_usage.return_value.percent = 50.0
        mock_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.net_io_counters.return_value = mock_net
        mock_pynvml.nvmlInit.side_effect = ImportError
        instance = SystemMonitor(config={})
        recs = instance.get_resource_recommendations()
        assert recs == {}

    @patch('monitoring.system_monitor.psutil')
    @patch('monitoring.system_monitor.pynvml')
    def test_stop_monitoring(self, mock_pynvml, mock_psutil):
        from monitoring.system_monitor import SystemMonitor
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 ** 3
        mock_psutil.disk_usage.return_value.used = 50
        mock_psutil.disk_usage.return_value.total = 100
        mock_psutil.disk_usage.return_value.percent = 50.0
        mock_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.net_io_counters.return_value = mock_net
        mock_pynvml.nvmlInit.side_effect = ImportError
        instance = SystemMonitor(config={})
        instance.stop_monitoring()
        assert instance.is_monitoring is False
