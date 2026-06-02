"""Tests for services/brain_bridge_service.py"""
from unittest.mock import patch, MagicMock
import pytest


class TestBrainBridgeService:
    """Tests for BrainBridgeService"""

    def test_import(self):
        from services.brain_bridge_service import BrainBridgeService
        assert BrainBridgeService is not None

    @patch('services.brain_bridge_service.SystemHardwareProbe')
    def test_instantiation(self, mock_probe):
        from services.brain_bridge_service import BrainBridgeService
        mock_digital_life = MagicMock()
        mock_probe.return_value = MagicMock()
        instance = BrainBridgeService(digital_life=mock_digital_life, metrics_path="test_metrics.md")
        assert instance is not None
        assert instance.metrics_path.name == "test_metrics.md"

    @patch('services.brain_bridge_service.SystemHardwareProbe')
    def test_get_current_status(self, mock_probe):
        from services.brain_bridge_service import BrainBridgeService
        mock_digital_life = MagicMock()
        mock_digital_life.get_formula_metrics.return_value = {"intelligence": 0.8}
        mock_digital_life.biological_integrator.get_biological_state.return_value = {"heart_rate": 72}
        mock_probe.return_value = MagicMock()
        mock_probe.return_value.detect.return_value = MagicMock(
            performance_tier="high", ai_capability_score=95, accelerator_type=MagicMock(value="cuda")
        )
        instance = BrainBridgeService(digital_life=mock_digital_life, metrics_path="test_metrics.md")
        status = instance.get_current_status()
        assert "brain" in status
        assert "biological" in status
        assert "hardware" in status
        assert "timestamp" in status
        assert status["brain"]["intelligence"] == 0.8

    @patch('services.brain_bridge_service.SystemHardwareProbe')
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_probe):
        from services.brain_bridge_service import BrainBridgeService
        mock_digital_life = MagicMock()
        mock_probe.return_value = MagicMock()
        instance = BrainBridgeService(digital_life=mock_digital_life, metrics_path="test_metrics.md")
        assert instance._running is False
        await instance.start()
        assert instance._running is True
        await instance.stop()
        assert instance._running is False
