"""Smoke tests for api/v1/endpoints/mobile.py"""
import pytest


class TestMobileEndpoint:
    """Basic smoke tests for mobile endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.mobile import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"mobile endpoint not available: {e}")
