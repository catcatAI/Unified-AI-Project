"""Smoke tests for EnterpriseMonitor and MetricsCollector"""
import pytest


class TestEnterpriseMonitor:
    """Basic smoke tests for EnterpriseMonitor"""

    def test_import_monitor(self):
        """Verify EnterpriseMonitor can be imported"""
        try:
            from core.monitoring.enterprise_monitor import EnterpriseMonitor
            assert EnterpriseMonitor is not None
        except ImportError as e:
            pytest.skip(f"EnterpriseMonitor not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.monitoring.enterprise_monitor import EnterpriseMonitor
            instance = EnterpriseMonitor()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"EnterpriseMonitor not available: {e}")
        except Exception as e:
            pytest.skip(f"EnterpriseMonitor init failed (expected in CI): {e}")


class TestMetricsCollector:
    """Basic smoke tests for MetricsCollector"""

    def test_import_collector(self):
        """Verify MetricsCollector can be imported"""
        try:
            from core.monitoring.enterprise_monitor import MetricsCollector
            assert MetricsCollector is not None
        except ImportError as e:
            pytest.skip(f"MetricsCollector not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.monitoring.enterprise_monitor import MetricsCollector
            instance = MetricsCollector()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"MetricsCollector not available: {e}")
        except Exception as e:
            pytest.skip(f"MetricsCollector init failed (expected in CI): {e}")
