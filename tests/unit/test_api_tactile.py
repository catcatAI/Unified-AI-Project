"""Tests for api/v1/endpoints/tactile.py"""
import pytest


class TestTactileEndpoint:
    """Tests for tactile endpoint module"""

    def test_import(self):
        from api.v1.endpoints.tactile import router
        assert router is not None
        assert router.prefix == "/tactile"
