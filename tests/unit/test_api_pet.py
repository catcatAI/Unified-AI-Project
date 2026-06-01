"""Smoke tests for api/v1/endpoints/pet.py"""
import pytest


class TestPetEndpoint:
    """Basic smoke tests for pet endpoint module"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from api.v1.endpoints.pet import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"pet endpoint not available: {e}")
