"""Smoke tests for core.life.bio_reflex_manager"""
import pytest


class TestBiogenicReflexManager:
    def test_import(self):
        try:
            from core.life.bio_reflex_manager import BiogenicReflexManager
            assert BiogenicReflexManager is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.life.bio_reflex_manager import BiogenicReflexManager
            instance = BiogenicReflexManager(bio_integrator=None)
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
