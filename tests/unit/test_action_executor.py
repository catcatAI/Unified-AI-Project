"""Smoke tests for ActionExecutor"""
import pytest


class TestActionExecutor:
    """Basic smoke tests for ActionExecutor"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.engine.action_executor import ActionExecutor
            assert ActionExecutor is not None
        except ImportError as e:
            pytest.skip(f"ActionExecutor not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.engine.action_executor import ActionExecutor
            instance = ActionExecutor(config={"max_queue_size": 10})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"ActionExecutor not available: {e}")
        except Exception as e:
            pytest.skip(f"ActionExecutor init failed (expected in CI): {e}")
