"""Tests for api/v1/endpoints/mobile.py"""
import pytest


class TestMobileEndpoint:
    """Tests for mobile endpoint module"""

    def test_import(self):
        from api.v1.endpoints.mobile import router
        assert router is not None
        assert router.prefix == "/mobile"
