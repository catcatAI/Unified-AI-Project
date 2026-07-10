"""Smoke tests for core.hardware.webgl_bridge"""
import pytest

pytest.importorskip("core.hardware.webgl_bridge")
from core.hardware.webgl_bridge import WebGLGPUInfo


class TestWebGLGPUInfo:
    def test_import(self):
        assert hasattr(WebGLGPUInfo, 'from_dict')
        assert hasattr(WebGLGPUInfo, 'to_uhrc_format')
        assert hasattr(WebGLGPUInfo, '_detect_gpu_type')
        assert hasattr(WebGLGPUInfo, '_estimate_memory')
        assert hasattr(WebGLGPUInfo, '_get_capabilities')

    def test_instantiation(self):
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

    def test_from_dict(self):
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


class TestWebGLBridge:
    def test_import(self):
        from core.hardware.webgl_bridge import WebGLBridge
        assert hasattr(WebGLBridge, 'process_gpu_info')
        assert hasattr(WebGLBridge, 'get_gpu_info')
        assert hasattr(WebGLBridge, 'is_synced')
        assert hasattr(WebGLBridge, 'get_summary')

    def test_instantiation(self):
        from core.hardware.webgl_bridge import WebGLBridge
        instance = WebGLBridge()
        assert instance._initialized is True
        assert instance._gpu_info is None
        assert instance._is_synced is False

        summary = instance.get_summary()
        assert summary["gpu_name"] is None
        assert summary["gpu_type"] is None
        assert summary["vendor"] is None
        assert summary["is_synced"] is False
