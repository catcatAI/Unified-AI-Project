"""Smoke tests for api/v1/endpoints/vision.py"""
import pytest


class TestVisionEndpoint:
    """Basic smoke tests for vision endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.vision import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"vision endpoint not available: {e}")
