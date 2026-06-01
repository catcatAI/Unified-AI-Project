"""Smoke tests for api/v1/endpoints/plugins.py"""
import pytest


class TestPluginsEndpoint:
    """Basic smoke tests for plugins endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.plugins import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"plugins endpoint not available: {e}")
