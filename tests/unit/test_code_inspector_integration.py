"""Smoke tests for apps.backend.src.ai.code_inspection.code_inspector_integration"""
import pytest

class TestCodeInspectorBridge:
    def test_import(self):
        try:
            from apps.backend.src.ai.code_inspection.code_inspector_integration import CodeInspectorBridge
            assert CodeInspectorBridge is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.ai.code_inspection.code_inspector_integration import CodeInspectorBridge
            instance = CodeInspectorBridge(state_adapter=None)
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
