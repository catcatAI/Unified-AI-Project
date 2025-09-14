import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent.parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

from apps.backend.src.ai.dialogue.project_coordinator import ProjectCoordinator

@pytest.fixture
def project_coordinator():
    """Provides a ProjectCoordinator instance with mocked dependencies."""
    mock_llm_interface = AsyncMock()
    mock_service_discovery = AsyncMock()  # 修改为AsyncMock
    mock_service_discovery.get_all_capabilities_async = AsyncMock(return_value=[])
    mock_hsp_connector = MagicMock()
    mock_agent_manager = MagicMock()
    mock_memory_manager = MagicMock()
    mock_learning_manager = AsyncMock()
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"

    # Mock the config dictionary
    mock_config = {
        "turn_timeout_seconds": 30
    }

    pc = ProjectCoordinator(
        llm_interface=mock_llm_interface,
        service_discovery=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,
        memory_manager=mock_memory_manager,
        learning_manager=mock_learning_manager,
        personality_manager=mock_personality_manager,
        dialogue_manager_config=mock_config
    )
    return pc

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_handle_project_happy_path(project_coordinator):
    """
    Tests the full, successful execution of a project from query to final response.
    This replaces the previous, overly mocked test.
    """
    # Arrange
    pc = project_coordinator
    user_query = "Build a website for me."
    decomposed_tasks = [
        {"capability_needed": "create_files_v1", "task_parameters": {"files": ["index.html"]}, "task_description": "Create a homepage."}
    ]
    execution_results = {0: {"status": "success", "result": "index.html created."}}
    final_integrated_response = "I have successfully created the index.html file for your website."
    
    # 正确模拟 service_discovery.get_all_capabilities_async() 的异步调用
    pc.service_discovery.get_all_capabilities_async.return_value = []

    # Mock the three main phases of the project
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=decomposed_tasks)
    pc._execute_task_graph = AsyncMock(return_value=execution_results)
    pc._integrate_subtask_results = AsyncMock(return_value=final_integrated_response)

    # Act
    response = await pc.handle_project(user_query, "session123", "user456")

    # Assert
    # 修复断言，确保正确检查异步方法的调用
    pc.service_discovery.get_all_capabilities_async.assert_awaited_once()
    pc._decompose_user_intent_into_subtasks.assert_awaited_once_with(user_query, [])
    pc._execute_task_graph.assert_awaited_once_with(decomposed_tasks)
    pc._integrate_subtask_results.assert_awaited_once_with(user_query, execution_results)

    # Verify learning manager was called
    pc.learning_manager.learn_from_project_case.assert_awaited_once()

    # Verify the final response is correctly formatted
    expected_response = f"TestAI: Here's the result of your project request:\n\n{final_integrated_response}"
    assert response == expected_response

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_handle_project_decomposition_fails(project_coordinator):
    """
    Tests that if task decomposition fails, a user-friendly message is returned.
    """
    # Arrange
    pc = project_coordinator
    # 正确模拟 service_discovery.get_all_capabilities_async() 的异步调用
    pc.service_discovery.get_all_capabilities_async.return_value = []
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=[]) # Simulate LLM failing to decompose

    # Patch the methods to check they were not called
    with patch.object(pc, '_execute_task_graph', new_callable=AsyncMock) as mock_execute:
        with patch.object(pc, '_integrate_subtask_results', new_callable=AsyncMock) as mock_integrate:
            # Act
            response = await pc.handle_project("An impossible task.", "s1", "u1")

            # Assert
            assert response == "TestAI: I couldn't break down your request into a clear plan."
            mock_execute.assert_not_called()
            mock_integrate.assert_not_called()

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_execute_task_graph_with_dependencies(project_coordinator):
    """
    Tests that _execute_task_graph correctly handles dependencies between tasks.
    """
    # Arrange
    pc = project_coordinator
    # Mock the actual dispatching logic
    pc._dispatch_single_subtask = AsyncMock(side_effect=[
        {"result": "Task 0 was successful"},
        {"result": "Task 1 was successful"}
    ])

    subtasks = [
        {"capability_needed": "task0_v1", "task_parameters": {"param": "A"}},
        {"capability_needed": "task1_v1", "task_parameters": {"input_data": "Some static data and <output_of_task_0>"}}
    ]

    # Act
    results = await pc._execute_task_graph(subtasks)

    # Assert
    assert len(results) == 2
    assert results[0] == {"result": "Task 0 was successful"}
    assert results[1] == {"result": "Task 1 was successful"}

    # Verify that the substitution happened correctly before dispatching the second task
    expected_call_for_task1 = call({
        'capability_needed': 'task1_v1',
        'task_parameters': {'input_data': 'Some static data and {"result": "Task 0 was successful"}'}
    })
    pc._dispatch_single_subtask.assert_has_calls([
        call(subtasks[0]),
        expected_call_for_task1
    ])

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_dispatch_single_subtask_agent_not_found(project_coordinator):
    """
    Tests that if an agent cannot be found or launched, an error is returned.
    """
    # Arrange
    pc = project_coordinator
    pc.service_discovery.find_capabilities = AsyncMock(return_value=[]) # 修改为AsyncMock并设置返回值
    pc.agent_manager.launch_agent.return_value = None # Launching fails

    subtask = {"capability_needed": "non_existent_capability_v1"}

    # Act
    result = await pc._dispatch_single_subtask(subtask)

    # Assert
    assert result == {"error": "Could not find or launch an agent with capability 'non_existent_capability_v1'."}

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_dispatch_single_subtask_agent_launch_and_discovery(project_coordinator):
    """
    Tests the logic for launching a new agent when a capability is not initially found.
    """
    # Arrange
    pc = project_coordinator
    capability_name = "needed_capability_v1"
    agent_name_to_launch = "needed_capability_agent"
    subtask = {"capability_needed": capability_name, "task_parameters": {}}

    # Mock the return value for the launched agent's capability
    new_capability_payload = {
        "capability_id": "cap_123",
        "ai_id": "agent_xyz",
        # ... other fields
    }

    # Simulate finding no capabilities initially, then finding one after launch
    pc.service_discovery.find_capabilities = AsyncMock(side_effect=[  # 修改为AsyncMock
        [], # First call: not found
        [new_capability_payload] # Second call: found
    ])

    # Mock a successful agent launch that returns a future
    mock_future = asyncio.Future()
    mock_future.set_result(True) # Simulate the agent becoming ready
    pc.agent_manager.launch_agent.return_value = mock_future

    # Mock the downstream HSP request and result waiting
    pc._send_hsp_request = AsyncMock(return_value=("Request sent.", "corr_123"))
    pc._wait_for_task_result = AsyncMock(return_value={"status": "success"})

    # Act
    result = await pc._dispatch_single_subtask(subtask)

    # Assert
    # Verify agent manager was called to launch the correct agent
    pc.agent_manager.launch_agent.assert_called_once_with(agent_name_to_launch)

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_wait_for_task_result_timeout(project_coordinator):
    """
    Tests that _wait_for_task_result correctly returns an error on timeout.
    """
    # Arrange
    pc = project_coordinator
    pc.turn_timeout_seconds = 0.01 # Set a very short timeout for the test

    # Act
    result = await pc._wait_for_task_result("corr_timeout", "timeout_capability")

    # Assert
    assert result == {"error": "Task for 'timeout_capability' timed out."}