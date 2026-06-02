"""Tests for api/v1/endpoints/trace.py"""
import pytest


class TestTraceEndpoint:
    """Tests for trace endpoint module"""

    def test_import(self):
        from api.v1.endpoints.trace import router
        assert router is not None
        assert router.prefix == "/trace"
