"""Tests for integrations/rovo_dev_connector.py"""
import pytest


class TestRovoDevConnector:
    """Tests for RovoDevConnector alias"""

    def test_import(self):
        from integrations.rovo_dev_connector import RovoDevConnector
        assert RovoDevConnector is not None

    def test_alias_to_enhanced(self):
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        from integrations.rovo_dev_connector import RovoDevConnector
        assert RovoDevConnector is EnhancedRovoDevConnector

    def test_instantiation(self):
        from integrations.rovo_dev_connector import RovoDevConnector
        instance = RovoDevConnector(config={})
        assert instance is not None
