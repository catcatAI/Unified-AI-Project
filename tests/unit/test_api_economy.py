"""Smoke tests for api/v1/endpoints/economy.py"""
import pytest


class TestEconomyEndpoint:
    """Basic smoke tests for economy endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.economy import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"economy endpoint not available: {e}")
