import asyncio
import pytest
from unittest.mock import AsyncMock

from ai.agents.base_agent import BaseAgent

pytestmark = pytest.mark.asyncio

class MockAgent(BaseAgent):
    """
    A concrete implementation of BaseAgent for testing,
    satisfying the abstract method requirements.
    The actual mock objects will be attached during test setup.
    """
    async def perceive(self, task):
        # This will be replaced by a mock in the test function
        await asyncio.sleep(0)
        return {}

    async def decide(self, perceived_info):
        await asyncio.sleep(0)
        return {}

    async def act(self, decision):
        await asyncio.sleep(0)
        return {}

    async def feedback(self, original_task, action_result):
        await asyncio.sleep(0)


async def test_handle_task_timeout_original_flaw():
    """
    This test is designed to fail with the original implementation
    and pass with the corrected one. It verifies that the timeout applies
    to the whole task execution, not just one part.
    """
    agent = MockAgent(name="TimeoutTestAgent", task_timeout=0.1)

    # This async function will be the side effect
    async def long_acting_process(*args, **kwargs):
        await asyncio.sleep(0.2)

    # Attach mocks for this specific test
    agent.perceive = AsyncMock(return_value={"perceived": True})
    agent.decide = AsyncMock(return_value={"decision": "go"})
    # Make the 'act' phase take longer than the individual stage timeout
    agent.act = AsyncMock(side_effect=long_acting_process)
    agent.feedback = AsyncMock()

    task = {"type": "long_task"}
    result = await agent.handle_task(task)

    # The original code has a per-stage timeout, so this *should* now correctly fail.
    # The test will pass, proving the flaw exists and is testable.
    assert result["status"] == "failed"
    assert "timed out" in result["error"]

    agent.perceive.assert_called_once()
    agent.decide.assert_called_once()
    agent.act.assert_called_once()
    agent.feedback.assert_not_called()


async def test_handle_task_completes_successfully():
    """Tests a task that completes within the timeout."""
    agent = MockAgent(name="SuccessTestAgent", task_timeout=1)

    # Attach mocks
    agent.perceive = AsyncMock(return_value={"perceived": True})
    agent.decide = AsyncMock(return_value={"decision": "go"})
    agent.act = AsyncMock(return_value={"acted": True})
    agent.feedback = AsyncMock()

    task = {"type": "quick_task"}
    result = await agent.handle_task(task)

    assert result["status"] == "completed"
    assert result["result"] == {"acted": True}

    agent.perceive.assert_called_once()
    agent.decide.assert_called_once()
    agent.act.assert_called_once()
    agent.feedback.assert_called_once()


async def test_general_exception_handling():
    """Tests that a non-timeout exception during the lifecycle is caught."""
    agent = MockAgent(name="ExceptionTestAgent", task_timeout=1)

    error_message = "A critical error occurred"
    # Attach mocks
    agent.perceive = AsyncMock(return_value={"perceived": True})
    agent.decide = AsyncMock(return_value={"decision": "go"})
    agent.act = AsyncMock(side_effect=Exception(error_message))
    agent.feedback = AsyncMock()

    task = {"type": "failing_task"}
    result = await agent.handle_task(task)

    assert result["status"] == "failed"
    assert result["error"] == error_message

    agent.feedback.assert_not_called()
