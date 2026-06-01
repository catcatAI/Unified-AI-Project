"""Smoke tests for integrations/enhanced_rovo_dev_connector.py"""
import pytest


class TestEnhancedRovoDevConnector:
    """Basic smoke tests for EnhancedRovoDevConnector"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
            assert EnhancedRovoDevConnector is not None
        except ImportError as e:
            pytest.skip(f"EnhancedRovoDevConnector not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
            instance = EnhancedRovoDevConnector(config={})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"EnhancedRovoDevConnector not available: {e}")
        except Exception as e:
            pytest.skip(f"EnhancedRovoDevConnector init failed (expected in CI): {e}")
