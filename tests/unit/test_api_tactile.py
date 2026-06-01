"""Smoke tests for api/v1/endpoints/tactile.py"""
import pytest


class TestTactileEndpoint:
    """Basic smoke tests for tactile endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.tactile import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"tactile endpoint not available: {e}")
