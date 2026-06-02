"""Tests for LISManager"""
import pytest
from unittest.mock import AsyncMock, Mock


class TestLISManager:
    def test_import(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        assert hasattr(LISManager, 'monitor_output')
        assert hasattr(LISManager, 'get_system_health')

    def test_instantiation(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        mock_cache = Mock()
        instance = LISManager(cache=mock_cache, config={"introspector_config": {}})
        assert instance.cache is mock_cache
        assert instance.config == {"introspector_config": {}}
        assert instance.introspector is not None

    @pytest.mark.asyncio
    async def test_monitor_output_no_anomalies(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        mock_cache = AsyncMock()
        mock_introspector = Mock()
        mock_introspector.analyze_output = AsyncMock(return_value=[])
        instance = LISManager(cache=mock_cache, config={})
        instance.introspector = mock_introspector
        result = await instance.monitor_output("test output", {"key": "val"})
        assert result == []
        mock_introspector.analyze_output.assert_called_once_with("test output", {"key": "val"})

    @pytest.mark.asyncio
    async def test_monitor_output_with_anomalies(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        mock_cache = AsyncMock()
        anomaly = {
            "anomaly_type": "HALLUCINATION",
            "description": "Test anomaly",
            "severity": 0.8
        }
        mock_introspector = Mock()
        mock_introspector.analyze_output = AsyncMock(return_value=[anomaly])
        instance = LISManager(cache=mock_cache, config={})
        instance.introspector = mock_introspector
        result = await instance.monitor_output("test output", {})
        assert len(result) == 1
        assert result[0] == anomaly
        mock_cache.store_incident.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_health_healthy(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        mock_cache = AsyncMock()
        mock_cache.query_incidents = AsyncMock(return_value=[])
        instance = LISManager(cache=mock_cache, config={})
        health = await instance.get_system_health()
        assert health["status"] == "HEALTHY"
        assert health["recent_incidents_count"] == 0

    @pytest.mark.asyncio
    async def test_get_system_health_observation(self):
        from apps.backend.src.ai.lis.lis_manager import LISManager
        mock_cache = AsyncMock()
        mock_cache.query_incidents = AsyncMock(return_value=[{"id": "inc_1"}])
        instance = LISManager(cache=mock_cache, config={})
        health = await instance.get_system_health()
        assert health["status"] == "OBSERVATION"
        assert health["recent_incidents_count"] == 1
