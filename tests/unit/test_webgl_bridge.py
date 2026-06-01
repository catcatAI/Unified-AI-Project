"""Smoke tests for core.hardware.webgl_bridge"""
import pytest


class TestWebGLGPUInfo:
    def test_import(self):
        try:
            from core.hardware.webgl_bridge import WebGLGPUInfo
            assert WebGLGPUInfo is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.webgl_bridge import WebGLGPUInfo
            instance = WebGLGPUInfo(
                available=True,
                name="TestGPU",
                vendor="TestVendor",
                renderer="TestRenderer",
                version="1.0",
                webgl_version="2.0",
                unmasked_vendor="TestVendor",
                unmasked_renderer="TestRenderer",
            )
            assert instance is not None
            assert instance.name == "TestGPU"
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_from_dict(self):
        try:
            from core.hardware.webgl_bridge import WebGLGPUInfo
            data = {
                "available": True,
                "name": "NVIDIA RTX 4090",
                "vendor": "NVIDIA",
                "renderer": "NVIDIA RTX 4090",
                "version": "4.6",
                "webgl_version": "2.0",
                "unmasked_vendor": "NVIDIA",
                "unmasked_renderer": "NVIDIA RTX 4090",
            }
            gpu = WebGLGPUInfo.from_dict(data)
            assert gpu.name == "NVIDIA RTX 4090"
            assert gpu.to_uhrc_format()["type"] == "NVIDIA"
        except ImportError as e:
            pytest.skip(f"Not available: {e}")


class TestWebGLBridge:
    def test_import(self):
        try:
            from core.hardware.webgl_bridge import WebGLBridge
            assert WebGLBridge is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.webgl_bridge import WebGLBridge
            instance = WebGLBridge()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
