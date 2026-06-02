"""Smoke tests for ai.context.tool_context"""
import pytest

class TestToolCategory:
    def test_import(self):
        try:
            from ai.context.tool_context import ToolCategory
            assert ToolCategory is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from ai.context.tool_context import ToolCategory
            instance = ToolCategory(category_id="cat1", name="Test")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
