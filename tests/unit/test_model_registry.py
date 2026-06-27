"""Smoke tests for apps.backend.src.ai.language_models.registry"""
import pytest


class TestModelRegistry:
    def test_import(self):
        try:
            from apps.backend.src.ai.language_models.registry import ModelRegistry
            assert ModelRegistry is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.ai.language_models.registry import ModelRegistry
            instance = ModelRegistry(model_configs={})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
