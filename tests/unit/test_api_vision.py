"""Tests for api/v1/endpoints/vision.py"""
import pytest


class TestVisionEndpoint:
    """Tests for vision endpoint module"""

    def test_import(self):
        from api.v1.endpoints.vision import router
        assert router is not None
        assert router.prefix == "/vision"
