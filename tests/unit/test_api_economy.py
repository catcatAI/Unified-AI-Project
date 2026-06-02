"""Tests for api/v1/endpoints/economy.py"""
import pytest


class TestEconomyEndpoint:
    """Tests for economy endpoint module"""

    def test_import(self):
        from api.v1.endpoints.economy import router
        assert router is not None
        assert router.prefix == "/economy"
