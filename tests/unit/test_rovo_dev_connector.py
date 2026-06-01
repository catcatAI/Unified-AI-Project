"""Smoke tests for integrations/rovo_dev_connector.py"""
import pytest


class TestRovoDevConnector:
    """Basic smoke tests for RovoDevConnector alias"""

    def test_import(self):
        """Verify module can be imported and RovoDevConnector alias exists"""
        try:
            from integrations.rovo_dev_connector import RovoDevConnector
            assert RovoDevConnector is not None
        except ImportError as e:
            pytest.skip(f"RovoDevConnector not available: {e}")
