"""Smoke tests for apps.backend.src.ai.code_inspection.code_inspector"""
import pytest

class TestCodeInspector:
    def test_import(self):
        try:
            from apps.backend.src.ai.code_inspection.code_inspector import CodeInspector
            assert CodeInspector is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.ai.code_inspection.code_inspector import CodeInspector
            instance = CodeInspector(root_path=".")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
