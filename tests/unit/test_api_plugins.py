"""Tests for api/v1/endpoints/plugins.py"""
import pytest


class TestPluginsEndpoint:
    """Tests for plugins endpoint module"""

    def test_import(self):
        from api.v1.endpoints.plugins import router
        assert router is not None
        assert router.prefix == "/plugins"
