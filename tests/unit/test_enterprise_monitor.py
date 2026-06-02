"""Tests for EnterpriseMonitor and MetricsCollector"""
import pytest
import asyncio


class TestEnterpriseMonitor:
    """Tests for EnterpriseMonitor"""

    def test_import_monitor(self):
        """Verify EnterpriseMonitor can be imported"""
        from core.monitoring.enterprise_monitor import EnterpriseMonitor, AlertLevel, Alert
        assert issubclass(EnterpriseMonitor, object)
        assert hasattr(EnterpriseMonitor, 'start')
        assert hasattr(EnterpriseMonitor, 'stop')
        assert hasattr(EnterpriseMonitor, 'raise_alert')
        assert hasattr(EnterpriseMonitor, 'get_alerts')
        assert hasattr(EnterpriseMonitor, 'record_metric')
        assert hasattr(EnterpriseMonitor, 'get_status')
        assert issubclass(AlertLevel, object)
        assert issubclass(Alert, object)

    def test_instantiation(self):
        """Verify basic instantiation and core workflows"""
        from core.monitoring.enterprise_monitor import EnterpriseMonitor, AlertLevel
        instance = EnterpriseMonitor()
        assert instance._running is False
        assert len(instance._alerts) == 0

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(instance.start())
            assert result is True
            assert instance.is_running() is True

            instance.record_metric("cpu_usage", 85.5)
            metrics = instance.get_metrics("cpu_usage")
            assert metrics["name"] == "cpu_usage"
            assert len(metrics["data"]) == 1
            assert metrics["data"][0]["value"] == 85.5

            all_metrics = instance.get_metrics()
            assert "cpu_usage" in all_metrics

            alert = instance.raise_alert(AlertLevel.WARNING, "High CPU usage", "test")
            assert alert.level == AlertLevel.WARNING
            assert alert.message == "High CPU usage"
            assert alert.acknowledged is False
            assert alert.source == "test"

            alerts = instance.get_alerts()
            assert len(alerts) == 1
            unacked = instance.get_alerts(acknowledged=False)
            assert len(unacked) == 1
            acked = instance.get_alerts(acknowledged=True)
            assert len(acked) == 0

            assert instance.acknowledge_alert(alert.id) is True
            assert instance.acknowledge_alert("nonexistent") is False

            status = instance.get_status()
            assert status["running"] is True
            assert status["alert_count"] == 1
            assert status["unacknowledged_count"] == 0
            assert "timestamp" in status

            loop.run_until_complete(instance.stop())
        finally:
            loop.close()


class TestMetricsCollector:
    """Tests for MetricsCollector"""

    def test_import_collector(self):
        """Verify MetricsCollector can be imported"""
        from core.monitoring.enterprise_monitor import MetricsCollector
        assert hasattr(MetricsCollector, 'record')
        assert hasattr(MetricsCollector, 'get')
        assert hasattr(MetricsCollector, 'get_all')

    def test_instantiation(self):
        """Verify basic instantiation and metric operations"""
        from core.monitoring.enterprise_monitor import MetricsCollector
        instance = MetricsCollector()
        assert instance._metrics == {}

        instance.record("cpu", 90.0)
        instance.record("cpu", 80.0)
        instance.record("memory", 4096.0)

        cpu_data = instance.get("cpu")
        assert len(cpu_data) == 2
        assert cpu_data[0]["value"] == 90.0
        assert cpu_data[1]["value"] == 80.0

        assert instance.get("nonexistent") == []

        all_metrics = instance.get_all()
        assert "cpu" in all_metrics
        assert "memory" in all_metrics
        assert len(all_metrics) == 2
