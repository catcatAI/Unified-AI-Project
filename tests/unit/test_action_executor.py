"""Tests for ActionExecutor"""
import pytest


class TestActionExecutor:
    """Tests for ActionExecutor"""

    def test_import(self):
        from core.engine.action_executor import ActionExecutor
        assert ActionExecutor is not None

    def test_import_enums(self):
        from core.engine.action_executor import ActionCategory, ActionPriority, ActionStatus
        assert ActionPriority is not None
        assert ActionStatus is not None
        assert ActionCategory is not None

    def test_action_priority_levels(self):
        from core.engine.action_executor import ActionPriority
        assert ActionPriority.CRITICAL.level == 0
        assert ActionPriority.HIGH.level == 1
        assert ActionPriority.NORMAL.level == 2
        assert ActionPriority.LOW.level == 3
        assert ActionPriority.BACKGROUND.level == 4

    def test_action_status_values(self):
        from core.engine.action_executor import ActionStatus
        assert ActionStatus.PENDING.en_name == "Pending"
        assert ActionStatus.COMPLETED.en_name == "Completed"
        assert ActionStatus.FAILED.en_name == "Failed"

    def test_instantiation(self):
        from core.engine.action_executor import ActionExecutor
        instance = ActionExecutor(config={"max_queue_size": 10})
        assert instance is not None
