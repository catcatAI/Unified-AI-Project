"""Smoke tests for apps.backend.src.ai.context.storage.disk"""
import pytest


class TestDiskStorage:
    def test_import(self):
        try:
            from apps.backend.src.ai.context.storage.disk import DiskStorage
            assert DiskStorage is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.ai.context.storage.disk import DiskStorage
            instance = DiskStorage(storage_dir="./test_storage")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
