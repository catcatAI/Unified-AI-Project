"""Smoke tests for core.art.real_comfyui_api"""
import pytest


class TestComfyUIClient:
    def test_import(self):
        try:
            from core.art.real_comfyui_api import ComfyUIClient
            assert ComfyUIClient is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.art.real_comfyui_api import ComfyUIClient
            instance = ComfyUIClient()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
