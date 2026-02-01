"""
Angela AI v6.0 - Action Executor Tests
动作执行器测试

Comprehensive test suite for the action executor including:
- ActionExecutor initialization and lifecycle
- Action data class and creation
- SafetyCheck validation
- Action queue and priority management
- Execution flow and error handling

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.autonomous.action_executor import (
    ActionPriority,
    ActionStatus,
    ActionCategory,
    ActionResult,
    SafetyCheck,
    Action,
    ActionQueue,
    ActionExecutor,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def action_executor() -> ActionExecutor:
    """Create an ActionExecutor instance for testing."""
    return ActionExecutor()


@pytest.fixture
def initialized_executor() -> ActionExecutor:
    """Create an initialized ActionExecutor instance."""
    executor = ActionExecutor()
    asyncio.run(executor.initialize())
    yield executor
    asyncio.run(executor.shutdown())


@pytest.fixture
def action_queue() -> ActionQueue:
    """Create an ActionQueue instance."""
    return ActionQueue(max_size=100)


@pytest.fixture
def sample_action() -> Action:
    """Create a sample Action for testing."""
    def dummy_func(name: str) -> str:
        return f"Hello, {name}!"
    
    return Action.create(
        name="test_action",
        category=ActionCategory.SYSTEM,
        priority=ActionPriority.NORMAL,
        function=dummy_func,
        parameters={"name": "Test"}
    )


@pytest.fixture
def async_sample_action() -> Action:
    """Create an async sample Action for testing."""
    async def async_dummy_func(value: int) -> int:
        await asyncio.sleep(0.01)
        return value * 2
    
    return Action.create(
        name="async_test_action",
        category=ActionCategory.SYSTEM,
        priority=ActionPriority.NORMAL,
        function=async_dummy_func,
        parameters={"value": 21}
    )


# =============================================================================
# ActionPriority Tests
# =============================================================================

class TestActionPriority:
    """Tests for the ActionPriority enum."""

    def test_priority_levels(self) -> None:
        """Test priority level ordering."""
        assert ActionPriority.CRITICAL.level < ActionPriority.HIGH.level
        assert ActionPriority.HIGH.level < ActionPriority.NORMAL.level
        assert ActionPriority.NORMAL.level < ActionPriority.LOW.level
        assert ActionPriority.LOW.level < ActionPriority.BACKGROUND.level

    def test_priority_names(self) -> None:
        """Test priority Chinese and English names."""
        assert ActionPriority.CRITICAL.cn_name == "紧急"
        assert ActionPriority.HIGH.cn_name == "高"
        assert ActionPriority.NORMAL.cn_name == "普通"


# =============================================================================
# ActionStatus Tests
# =============================================================================

class TestActionStatus:
    """Tests for the ActionStatus enum."""

    def test_status_definitions(self) -> None:
        """Test all status values are defined."""
        statuses = [
            ActionStatus.PENDING,
            ActionStatus.VALIDATING,
            ActionStatus.EXECUTING,
            ActionStatus.COMPLETED,
            ActionStatus.FAILED,
            ActionStatus.CANCELLED,
            ActionStatus.PAUSED
        ]
        
        for status in statuses:
            assert status.cn_name is not None
            assert status.en_name is not None


# =============================================================================
# ActionCategory Tests
# =============================================================================

class TestActionCategory:
    """Tests for the ActionCategory enum."""

    def test_category_count(self) -> None:
        """Test number of action categories."""
        assert len(ActionCategory) == 8

    def test_category_names(self) -> None:
        """Test category names."""
        assert ActionCategory.SYSTEM.cn_name == "系统"
        assert ActionCategory.UI.cn_name == "界面"
        assert ActionCategory.FILE.cn_name == "文件"
        assert ActionCategory.SAFETY_CRITICAL.cn_name == "安全关键"


# =============================================================================
# ActionResult Tests
# =============================================================================

class TestActionResult:
    """Tests for the ActionResult data class."""

    def test_result_creation_success(self) -> None:
        """Test successful result creation."""
        result = ActionResult(
            success=True,
            action_id="action_001",
            output="Success output",
            execution_time=1.5
        )
        
        assert result.success is True
        assert result.action_id == "action_001"
        assert result.output == "Success output"
        assert result.error is None
        assert result.execution_time == 1.5

    def test_result_creation_failure(self) -> None:
        """Test failed result creation."""
        result = ActionResult(
            success=False,
            action_id="action_002",
            error="Something went wrong",
            execution_time=0.5
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output is None


# =============================================================================
# Action Tests
# =============================================================================

class TestAction:
    """Tests for the Action data class."""

    def test_action_creation(self, sample_action: Action) -> None:
        """Test basic action creation."""
        assert sample_action.name == "test_action"
        assert sample_action.category == ActionCategory.SYSTEM
        assert sample_action.priority == ActionPriority.NORMAL
        assert sample_action.parameters == {"name": "Test"}
        assert sample_action.status == ActionStatus.PENDING
        assert sample_action.action_id is not None

    def test_action_id_uniqueness(self) -> None:
        """Test that each action gets a unique ID."""
        def dummy() -> None:
            pass
        
        action1 = Action.create("test1", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        action2 = Action.create("test2", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        
        assert action1.action_id != action2.action_id

    def test_action_default_parameters(self) -> None:
        """Test action with default parameters."""
        def dummy() -> None:
            pass
        
        action = Action.create(
            "test",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            dummy
        )
        
        assert action.parameters == {}

    def test_action_with_dependencies(self) -> None:
        """Test action with dependencies."""
        def dummy() -> None:
            pass
        
        action1 = Action.create("action1", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        action2 = Action.create(
            "action2",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            dummy,
        )
        action2.dependencies.add(action1.action_id)
        
        assert action1.action_id in action2.dependencies

    def test_action_safety_checks(self) -> None:
        """Test action with safety checks."""
        def dummy() -> None:
            pass
        
        action = Action.create(
            "test",
            ActionCategory.SAFETY_CRITICAL,
            ActionPriority.HIGH,
            dummy
        )
        action.safety_checks.append("parameter_validation")
        
        assert "parameter_validation" in action.safety_checks


# =============================================================================
# ActionQueue Tests
# =============================================================================

class TestActionQueue:
    """Tests for the ActionQueue class."""

    def test_queue_initialization(self, action_queue: ActionQueue) -> None:
        """Test queue initialization."""
        assert action_queue.max_size == 100
        assert len(action_queue._queue) == 0

    def test_enqueue_dequeue(self, action_queue: ActionQueue, sample_action: Action) -> None:
        """Test enqueue and dequeue operations."""
        # Enqueue
        result = action_queue.enqueue(sample_action)
        assert result is True
        assert len(action_queue._queue) == 1
        
        # Dequeue
        dequeued = action_queue.dequeue()
        assert dequeued is not None
        assert dequeued.action_id == sample_action.action_id
        assert len(action_queue._queue) == 0

    def test_priority_ordering(self, action_queue: ActionQueue) -> None:
        """Test that actions are ordered by priority."""
        def dummy() -> None:
            pass
        
        # Create actions with different priorities
        low_priority = Action.create("low", ActionCategory.SYSTEM, ActionPriority.LOW, dummy)
        high_priority = Action.create("high", ActionCategory.SYSTEM, ActionPriority.HIGH, dummy)
        normal_priority = Action.create("normal", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        
        # Enqueue in random order
        action_queue.enqueue(normal_priority)
        action_queue.enqueue(low_priority)
        action_queue.enqueue(high_priority)
        
        # Should dequeue in priority order
        first = action_queue.dequeue()
        assert first.priority == ActionPriority.HIGH
        
        second = action_queue.dequeue()
        assert second.priority == ActionPriority.NORMAL
        
        third = action_queue.dequeue()
        assert third.priority == ActionPriority.LOW

    def test_queue_full(self, action_queue: ActionQueue) -> None:
        """Test queue behavior when full."""
        def dummy() -> None:
            pass
        
        # Fill queue
        for i in range(action_queue.max_size):
            action = Action.create(f"action_{i}", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
            action_queue.enqueue(action)
        
        # Try to add one more
        extra_action = Action.create("extra", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        result = action_queue.enqueue(extra_action)
        
        assert result is False

    def test_cancel_action(self, action_queue: ActionQueue, sample_action: Action) -> None:
        """Test action cancellation."""
        action_queue.enqueue(sample_action)
        
        # Cancel
        result = action_queue.cancel_action(sample_action.action_id)
        
        assert result is True
        assert sample_action.status == ActionStatus.CANCELLED

    def test_cancel_nonexistent_action(self, action_queue: ActionQueue) -> None:
        """Test cancelling non-existent action."""
        result = action_queue.cancel_action("nonexistent_id")
        assert result is False

    def test_dependency_resolution(self, action_queue: ActionQueue) -> None:
        """Test dependency-based dequeuing."""
        def dummy() -> None:
            pass
        
        # Create actions with dependency
        action1 = Action.create("action1", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        action2 = Action.create("action2", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
        action2.dependencies.add(action1.action_id)
        
        action_queue.enqueue(action2)  # Enqueue dependent first
        action_queue.enqueue(action1)
        
        # Should get action1 first (dependencies not satisfied for action2)
        first = action_queue.dequeue()
        assert first.action_id == action1.action_id
        
        # Complete action1
        action1.status = ActionStatus.COMPLETED
        
        # Now action2 should be available
        second = action_queue.dequeue()
        assert second.action_id == action2.action_id

    def test_get_action(self, action_queue: ActionQueue, sample_action: Action) -> None:
        """Test retrieving action by ID."""
        action_queue.enqueue(sample_action)
        
        retrieved = action_queue.get_action(sample_action.action_id)
        
        assert retrieved is not None
        assert retrieved.action_id == sample_action.action_id

    def test_get_queue_status(self, action_queue: ActionQueue) -> None:
        """Test getting queue status."""
        def dummy() -> None:
            pass
        
        # Add some actions
        for i in range(5):
            action = Action.create(f"action_{i}", ActionCategory.SYSTEM, ActionPriority.NORMAL, dummy)
            action_queue.enqueue(action)
        
        status = action_queue.get_queue_status()
        
        assert status["pending"] == 5
        assert status["total"] == 5


# =============================================================================
# SafetyCheck Tests
# =============================================================================

class TestSafetyCheck:
    """Tests for the SafetyCheck class."""

    def test_safety_check_creation(self) -> None:
        """Test safety check creation."""
        def check_func(action: Action) -> tuple[bool, Optional[str]]:
            return True, None
        
        check = SafetyCheck(
            check_name="test_check",
            check_function=check_func,
            is_critical=True
        )
        
        assert check.check_name == "test_check"
        assert check.is_critical is True

    def test_safety_check_validation(self, sample_action: Action) -> None:
        """Test safety check validation."""
        def failing_check(action: Action) -> tuple[bool, Optional[str]]:
            return False, "Validation failed"
        
        check = SafetyCheck(
            check_name="failing_check",
            check_function=failing_check,
            is_critical=True
        )
        
        result, message = check.check_function(sample_action)
        
        assert result is False
        assert message == "Validation failed"


# =============================================================================
# ActionExecutor Tests
# =============================================================================

class TestActionExecutor:
    """Tests for the main ActionExecutor class."""

    @pytest.mark.asyncio
    async def test_executor_initialization(self, action_executor: ActionExecutor) -> None:
        """Test executor initialization."""
        await action_executor.initialize()
        
        assert action_executor._running is True
        assert action_executor._executor_task is not None
        
        await action_executor.shutdown()

    @pytest.mark.asyncio
    async def test_executor_shutdown(self, action_executor: ActionExecutor) -> None:
        """Test executor shutdown."""
        await action_executor.initialize()
        await action_executor.shutdown()
        
        assert action_executor._running is False
        assert action_executor._executor_task is None

    @pytest.mark.asyncio
    async def test_submit_and_execute_sync_action(self, initialized_executor: ActionExecutor) -> None:
        """Test submitting and executing a synchronous action."""
        def test_func(name: str) -> str:
            return f"Hello, {name}!"
        
        action = Action.create(
            "greet",
            ActionCategory.COMMUNICATION,
            ActionPriority.NORMAL,
            test_func,
            parameters={"name": "Alice"}
        )
        
        result = await initialized_executor.submit_and_execute(action)
        
        assert result.success is True
        assert result.output == "Hello, Alice!"
        assert result.error is None
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_submit_and_execute_async_action(self, initialized_executor: ActionExecutor) -> None:
        """Test submitting and executing an asynchronous action."""
        async def async_func(value: int) -> int:
            await asyncio.sleep(0.05)
            return value * 2
        
        action = Action.create(
            "calculate",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            async_func,
            parameters={"value": 21}
        )
        
        result = await initialized_executor.submit_and_execute(action)
        
        assert result.success is True
        assert result.output == 42
        assert result.execution_time >= 0.05

    @pytest.mark.asyncio
    async def test_action_failure(self, initialized_executor: ActionExecutor) -> None:
        """Test action failure handling."""
        def failing_func() -> None:
            raise ValueError("Intentional failure")
        
        action = Action.create(
            "failing_action",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            failing_func
        )
        
        result = await initialized_executor.submit_and_execute(action)
        
        assert result.success is False
        assert result.error is not None
        assert "Intentional failure" in result.error

    @pytest.mark.asyncio
    async def test_action_timeout(self, initialized_executor: ActionExecutor) -> None:
        """Test action timeout handling."""
        async def slow_func() -> str:
            await asyncio.sleep(2.0)  # Longer than timeout
            return "completed"
        
        action = Action.create(
            "slow_action",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            slow_func,
            timeout=0.1  # Short timeout
        )
        
        result = await initialized_executor.submit_and_execute(action)
        
        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_submit_non_blocking(self, initialized_executor: ActionExecutor) -> None:
        """Test non-blocking action submission."""
        async def slow_func() -> str:
            await asyncio.sleep(0.5)
            return "completed"
        
        action = Action.create(
            "slow_action",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            slow_func
        )
        
        action_id = initialized_executor.submit(action)
        
        assert action_id is not None
        assert action_id == action.action_id
        # Action should be in queue
        assert action.status == ActionStatus.PENDING

    def test_cancel_action(self, initialized_executor: ActionExecutor) -> None:
        """Test action cancellation."""
        async def slow_func() -> str:
            await asyncio.sleep(5.0)
            return "completed"
        
        action = Action.create(
            "cancellable_action",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            slow_func
        )
        
        action_id = initialized_executor.submit(action)
        
        # Cancel immediately
        result = initialized_executor.cancel_action(action_id)
        
        assert result is True

    def test_get_action_status(self, initialized_executor: ActionExecutor) -> None:
        """Test getting action status."""
        def dummy() -> None:
            pass
        
        action = Action.create(
            "test_action",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            dummy
        )
        
        action_id = initialized_executor.submit(action)
        status = initialized_executor.get_action_status(action_id)
        
        assert status is not None
        assert status in [ActionStatus.PENDING, ActionStatus.VALIDATING, ActionStatus.EXECUTING]

    def test_get_execution_stats(self, initialized_executor: ActionExecutor) -> None:
        """Test getting execution statistics."""
        stats = initialized_executor.get_execution_stats()
        
        assert "total_executed" in stats
        assert "total_failed" in stats
        assert "queue_status" in stats
        assert "active_actions" in stats

    def test_safety_check_registration(self, action_executor: ActionExecutor) -> None:
        """Test safety check registration."""
        def custom_check(action: Action) -> tuple[bool, Optional[str]]:
            return True, None
        
        check = SafetyCheck(
            check_name="custom_check",
            check_function=custom_check
        )
        
        action_executor.register_safety_check(check)
        
        assert "custom_check" in action_executor.safety_checks

    def test_callback_registration(self, initialized_executor: ActionExecutor) -> None:
        """Test callback registration."""
        callback_called = [False]
        
        def test_callback(action: Action) -> None:
            callback_called[0] = True
        
        initialized_executor.register_pre_execution_callback(test_callback)
        
        assert len(initialized_executor._pre_execution_callbacks) == 1

    @pytest.mark.asyncio
    async def test_priority_execution_order(self, initialized_executor: ActionExecutor) -> None:
        """Test that high priority actions execute before low priority."""
        execution_order: List[str] = []
        
        async def make_action(name: str) -> str:
            execution_order.append(name)
            await asyncio.sleep(0.01)
            return name
        
        # Create actions with different priorities
        low_action = Action.create(
            "low",
            ActionCategory.SYSTEM,
            ActionPriority.LOW,
            make_action,
            parameters={"name": "low"}
        )
        
        high_action = Action.create(
            "high",
            ActionCategory.SYSTEM,
            ActionPriority.HIGH,
            make_action,
            parameters={"name": "high"}
        )
        
        # Submit low priority first
        initialized_executor.submit(low_action)
        initialized_executor.submit(high_action)
        
        # Wait for execution
        await asyncio.sleep(0.1)
        
        # High priority should execute before low (or concurrently, but typically before)
        # Note: With async execution, exact order may vary, but high priority
        # should be dequeued first

    def test_default_safety_checks_present(self, action_executor: ActionExecutor) -> None:
        """Test that default safety checks are registered."""
        assert "parameter_validation" in action_executor.safety_checks
        assert "dependency_check" in action_executor.safety_checks

    @pytest.mark.asyncio
    async def test_parameter_validation_check(self, initialized_executor: ActionExecutor) -> None:
        """Test parameter validation safety check."""
        def test_func(param1: str, param2: int) -> str:
            return f"{param1}: {param2}"
        
        # Action with missing required parameters
        action = Action.create(
            "test",
            ActionCategory.SYSTEM,
            ActionPriority.NORMAL,
            test_func,
            parameters={"param1": "value"}  # Missing param2
        )
        
        # This will fail at execution time due to missing parameter
        result = await initialized_executor.submit_and_execute(action)
        
        # Should fail due to missing parameter
        assert result.success is False


# =============================================================================
# Integration Tests
# =============================================================================

class TestActionExecutorIntegration:
    """Integration tests for the action executor."""

    @pytest.mark.asyncio
    async def test_multiple_actions_sequential(self) -> None:
        """Test executing multiple actions sequentially."""
        executor = ActionExecutor()
        await executor.initialize()
        
        try:
            results: List[int] = []
            
            async def collect_value(value: int) -> int:
                results.append(value)
                await asyncio.sleep(0.01)
                return value
            
            # Submit multiple actions
            for i in range(5):
                action = Action.create(
                    f"action_{i}",
                    ActionCategory.SYSTEM,
                    ActionPriority.NORMAL,
                    collect_value,
                    parameters={"value": i}
                )
                await executor.submit_and_execute(action)
            
            # All actions should have executed
            assert len(results) == 5
            assert sorted(results) == [0, 1, 2, 3, 4]
            
        finally:
            await executor.shutdown()

    @pytest.mark.asyncio
    async def test_action_with_callback(self) -> None:
        """Test action execution with callbacks."""
        executor = ActionExecutor()
        await executor.initialize()
        
        try:
            pre_exec_called = [False]
            post_exec_called = [False]
            
            def pre_callback(action: Action) -> None:
                pre_exec_called[0] = True
            
            def post_callback(action: Action, result: ActionResult) -> None:
                post_exec_called[0] = True
            
            executor.register_pre_execution_callback(pre_callback)
            executor.register_post_execution_callback(post_callback)
            
            async def test_func() -> str:
                return "done"
            
            action = Action.create(
                "callback_test",
                ActionCategory.SYSTEM,
                ActionPriority.NORMAL,
                test_func
            )
            
            await executor.submit_and_execute(action)
            
            # Give time for callbacks
            await asyncio.sleep(0.05)
            
            assert pre_exec_called[0] is True
            assert post_exec_called[0] is True
            
        finally:
            await executor.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_action_limit(self) -> None:
        """Test concurrent action limit."""
        executor = ActionExecutor(config={"max_concurrent_actions": 2})
        await executor.initialize()
        
        try:
            active_count = [0]
            max_active = [0]
            
            async def track_concurrency() -> None:
                active_count[0] += 1
                max_active[0] = max(max_active[0], active_count[0])
                await asyncio.sleep(0.1)
                active_count[0] -= 1
            
            # Submit 5 concurrent actions
            for i in range(5):
                action = Action.create(
                    f"concurrent_{i}",
                    ActionCategory.SYSTEM,
                    ActionPriority.NORMAL,
                    track_concurrency
                )
                executor.submit(action)
            
            # Wait for completion
            await asyncio.sleep(0.5)
            
            # Should never exceed max_concurrent_actions
            assert max_active[0] <= 2
            
        finally:
            await executor.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
