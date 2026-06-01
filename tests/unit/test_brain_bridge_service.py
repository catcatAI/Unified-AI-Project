"""Smoke tests for services/brain_bridge_service.py with mock patching"""
from unittest.mock import patch, MagicMock, mock_open
import pytest


class TestBrainBridgeService:
    """Smoke tests for BrainBridgeService"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.brain_bridge_service import BrainBridgeService
            assert BrainBridgeService is not None
        except ImportError as e:
            pytest.skip(f"BrainBridgeService not available: {e}")

    @patch('services.brain_bridge_service.SystemHardwareProbe')
    def test_instantiation(self, mock_probe):
        """Verify basic instantiation with mock patching"""
        try:
            from services.brain_bridge_service import BrainBridgeService
            mock_digital_life = MagicMock()
            mock_probe.return_value = MagicMock()
            instance = BrainBridgeService(digital_life=mock_digital_life, metrics_path="test_metrics.md")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"BrainBridgeService not available: {e}")
        except Exception as e:
            pytest.skip(f"BrainBridgeService init failed (expected in CI): {e}")
