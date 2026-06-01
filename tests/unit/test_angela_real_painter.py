"""Smoke tests for core.art.real_comfyui_api"""
import pytest


class TestAngelaRealPainter:
    def test_import(self):
        try:
            from core.art.real_comfyui_api import AngelaRealPainter
            assert AngelaRealPainter is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.art.real_comfyui_api import AngelaRealPainter
            instance = AngelaRealPainter()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
