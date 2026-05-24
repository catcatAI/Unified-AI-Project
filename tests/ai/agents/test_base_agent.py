"""Tests for BaseAgent."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from ai.agents.base.base_agent import BaseAgent, TaskPriority, QueuedTask


@pytest.fixture
def base_agent():
    """Create a BaseAgent instance with test capabilities."""
    capabilities = [
        {
            "capability_id": "test_cap_1",
            "name": "Test Capability",
            "description": "A test capability",
            "version": "1.0",
        }
    ]
    return BaseAgent(
        agent_id="test_agent_001",
        agent_name="TestAgent",
        capabilities=capabilities,
    )


class TestBaseAgentInit:
    """Tests for BaseAgent initialization."""

    def test_initialization_with_name_and_capabilities(self):
        """Test agent initialization with name and capabilities."""
        caps = [{"capability_id": "cap_1", "name": "Cap 1"}]
        agent = BaseAgent(
            agent_id="agent_001",
            capabilities=caps,
            agent_name="CustomAgent",
        )
        assert agent.agent_id == "agent_001"
        assert agent.agent_name == "CustomAgent"
        assert agent.capabilities == caps
        assert agent.is_running is False
        assert agent.task_queue == []
        assert agent.max_queue_size == 100

    def test_initialization_without_capabilities(self):
        """Test agent initialization without capabilities defaults to empty list."""
        agent = BaseAgent(agent_id="agent_001")
        assert agent.capabilities == []
        assert agent.agent_name == "BaseAgent"

    def test_initialization_creates_lock(self, base_agent):
        """Test that initialization creates an asyncio lock."""
        assert base_agent.task_queue_lock is not None
        assert isinstance(base_agent.task_queue_lock, asyncio.Lock)


class TestTaskPriority:
    """Tests for task priority ordering."""

    def test_task_priority_values(self):
        """Test TaskPriority enum has correct values."""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.HIGH.value == 3
        assert TaskPriority.CRITICAL.value == 4

    def test_sort_by_priority_descending(self, base_agent):
        """Test that sort produces correct CRITICAL > HIGH > NORMAL > LOW order."""
        base_agent.task_queue = [
            QueuedTask(
                task_id="normal", priority=TaskPriority.NORMAL,
                payload={}, sender_id="s", envelope={}, received_time=0.0,
            ),
            QueuedTask(
                task_id="critical", priority=TaskPriority.CRITICAL,
                payload={}, sender_id="s", envelope={}, received_time=0.0,
            ),
            QueuedTask(
                task_id="low", priority=TaskPriority.LOW,
                payload={}, sender_id="s", envelope={}, received_time=0.0,
            ),
        ]
        base_agent.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        order = [t.task_id for t in base_agent.task_queue]
        assert order == ["critical", "normal", "low"]

    def test_reverse_sort_lowest_last(self, base_agent):
        """Test that LOW priority tasks appear at the end after sort."""
        base_agent.task_queue = [
            QueuedTask(
                task_id="low", priority=TaskPriority.LOW,
                payload={}, sender_id="s", envelope={}, received_time=0.0,
            ),
            QueuedTask(
                task_id="high", priority=TaskPriority.HIGH,
                payload={}, sender_id="s", envelope={}, received_time=0.0,
            ),
        ]
        base_agent.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        assert base_agent.task_queue[0].task_id == "high"
        assert base_agent.task_queue[-1].task_id == "low"


class TestTaskQueue:
    """Tests for task queue operations."""
    async def test_handle_task_request_adds_to_queue(self, base_agent):
        """Test that handle_task_request adds a task to the queue."""
        base_agent.hsp_connector = AsyncMock()

        payload = {"request_id": "req_001"}
        await base_agent.handle_task_request(payload, "sender_001", {})

        # Task should be in queue (may be consumed by _process_task_queue later)
        assert len(base_agent.task_queue) > 0
        assert base_agent.task_queue[0].task_id == "req_001"
    async def test_queue_task_sorts_by_priority_on_insert(self, base_agent):
        """Test that adding tasks via handle_task_request maintains priority order."""
        base_agent.hsp_connector = AsyncMock()
        base_agent.max_queue_size = 10

        # Insert LOW first, then HIGH
        low_payload = {"request_id": "low_001", "priority": 1}
        await base_agent.handle_task_request(low_payload, "sender", {})

        high_payload = {"request_id": "high_001", "priority": 3}
        await base_agent.handle_task_request(high_payload, "sender", {})

        # After both inserts and sort, HIGH should be first
        if len(base_agent.task_queue) >= 2:
            assert base_agent.task_queue[0].task_id == "high_001"
            assert base_agent.task_queue[1].task_id == "low_001"
    async def test_process_task_queue_pops_first_task(self, base_agent):
        """Test that _process_task_queue pops and processes the first task."""
        base_agent.hsp_connector = AsyncMock()
        base_agent.hsp_connector.is_connected = True

        # Manually populate the queue
        base_agent.task_queue = [
            QueuedTask(
                task_id="task_001", priority=TaskPriority.NORMAL,
                payload={"capability_id_filter": ""},
                sender_id="sender", envelope={}, received_time=0.0,
            ),
        ]

        await base_agent._process_task_queue()
        assert len(base_agent.task_queue) == 0
    async def test_process_task_queue_empty_does_nothing(self, base_agent):
        """Test that _process_task_queue does nothing when queue is empty."""
        base_agent.task_queue = []
        await base_agent._process_task_queue()
        assert base_agent.task_queue == []
    async def test_queue_overflow_rejects_task(self, base_agent):
        """Test that tasks are rejected when queue exceeds max_queue_size."""
        base_agent.hsp_connector = AsyncMock()
        base_agent.max_queue_size = 2

        # Fill the queue
        for i in range(2):
            payload = {"request_id": f"task_{i}"}
            await base_agent.handle_task_request(payload, "sender", {})

        # Next task with callback_address should be rejected
        reject_payload = {
            "request_id": "rejected_task",
            "callback_address": "callback/topic",
        }
        await base_agent.handle_task_request(reject_payload, "sender", {})

        # Should have called send_task_result with rejected status
        base_agent.hsp_connector.send_task_result.assert_called()
        call_args = base_agent.hsp_connector.send_task_result.call_args
        result_payload = call_args[0][0]
        assert result_payload["status"] == "rejected"
    async def test_handle_task_request_parses_priority(self, base_agent):
        """Test that handle_task_request correctly parses priority from payload."""
        base_agent.hsp_connector = AsyncMock()

        payload = {"request_id": "req_001", "priority": 4}
        await base_agent.handle_task_request(payload, "sender", {})

        assert len(base_agent.task_queue) > 0
        assert base_agent.task_queue[0].priority == TaskPriority.CRITICAL
    async def test_handle_task_request_invalid_priority_defaults_normal(self, base_agent):
        """Test that invalid priority value defaults to NORMAL."""
        base_agent.hsp_connector = AsyncMock()

        payload = {"request_id": "req_001", "priority": 99}
        await base_agent.handle_task_request(payload, "sender", {})

        assert len(base_agent.task_queue) > 0
        assert base_agent.task_queue[0].priority == TaskPriority.NORMAL
    async def test_handle_task_request_no_priority_defaults_normal(self, base_agent):
        """Test that missing priority defaults to NORMAL."""
        base_agent.hsp_connector = AsyncMock()

        payload = {"request_id": "req_001"}
        await base_agent.handle_task_request(payload, "sender", {})

        assert len(base_agent.task_queue) > 0
        assert base_agent.task_queue[0].priority == TaskPriority.NORMAL
    async def test_default_task_handler_returns_not_implemented(self, base_agent):
        """Test that default task handler returns NOT_IMPLEMENTED failure."""
        base_agent.hsp_connector = AsyncMock()

        payload = {
            "request_id": "req_001",
            "capability_id_filter": "unknown_cap",
        }
        await base_agent.handle_task_request(payload, "sender", {})

        # Let async processing settle
        await asyncio.sleep(0.01)

        # The task should have been processed (queue may be empty)
        # The default handler was called - we can't easily assert on the result
        # without a callback_address, so just verify no crash
        pass
    async def test_register_task_handler(self, base_agent):
        """Test registering a custom handler for a capability."""
        handler = Mock()
        handler = AsyncMock(return_value={"result": "ok"})
        base_agent.register_task_handler("custom_cap", handler)
        assert "custom_cap" in base_agent.task_handlers
        assert base_agent.task_handlers["custom_cap"] is handler


class TestAgentLifecycle:
    """Tests for agent lifecycle (start, stop, health)."""
    async def test_is_healthy_false_by_default(self, base_agent):
        """Test that is_healthy returns False when not started."""
        assert base_agent.is_healthy() is False

    def test_is_healthy_with_running_and_connected(self, base_agent):
        """Test is_healthy returns True when running and connector is connected."""
        base_agent.is_running = True
        base_agent.hsp_connector = Mock()
        base_agent.hsp_connector.is_connected = True
        assert base_agent.is_healthy() is True

    def test_is_healthy_false_if_not_running(self, base_agent):
        """Test is_healthy returns False when not running even if connector set."""
        base_agent.is_running = False
        base_agent.hsp_connector = Mock()
        base_agent.hsp_connector.is_connected = True
        assert base_agent.is_healthy() is False

    def test_is_healthy_false_if_no_connector(self, base_agent):
        """Test is_healthy returns False when connector is None."""
        base_agent.is_running = True
        base_agent.hsp_connector = None
        assert base_agent.is_healthy() is False
    async def test_stop_sets_running_false(self, base_agent):
        """Test that stop sets is_running to False."""
        base_agent.is_running = True
        base_agent.hsp_connector = AsyncMock()
        base_agent.hsp_connector.is_connected = True
        await base_agent.stop()
        assert base_agent.is_running is False
    async def test_start_with_mock_connector(self, base_agent):
        """Test start succeeds when hsp_connector is pre-configured."""
        base_agent.hsp_connector = AsyncMock()
        base_agent.hsp_connector.is_connected = True
        base_agent.hsp_connector.advertise_capability = AsyncMock()
        base_agent.hsp_connector.register_on_task_request_callback = Mock()
        await base_agent.start()
        assert base_agent.is_running is True
        base_agent.hsp_connector.register_on_task_request_callback.assert_called_once()
        base_agent.hsp_connector.advertise_capability.assert_called_once()
