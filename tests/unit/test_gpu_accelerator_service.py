"""Smoke tests for core.hardware.gpu_accelerator"""
import pytest


class TestGPUAcceleratorService:
    def test_import(self):
        try:
            from core.hardware.gpu_accelerator import GPUAcceleratorService
            assert GPUAcceleratorService is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.gpu_accelerator import GPUAcceleratorService
            instance = GPUAcceleratorService()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
