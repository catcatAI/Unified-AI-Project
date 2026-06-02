"""Tests for api/v1/endpoints/pet.py"""
import pytest


class TestPetEndpoint:
    """Tests for pet endpoint module"""

    def test_import(self):
        from api.v1.endpoints.pet import router
        assert router is not None
        assert router.prefix == "/pet"
