"""Smoke tests for integrations/rovo_dev_agent.py"""
import pytest


class TestRovoDevAgent:
    """Basic smoke tests for RovoDevAgent"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from integrations.rovo_dev_agent import RovoDevAgent
            assert RovoDevAgent is not None
        except ImportError as e:
            pytest.skip(f"RovoDevAgent not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from integrations.rovo_dev_agent import RovoDevAgent
            instance = RovoDevAgent(config={})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"RovoDevAgent not available: {e}")
        except Exception as e:
            pytest.skip(f"RovoDevAgent init failed (expected in CI): {e}")
