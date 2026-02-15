"""
Tests for the ProjectCoordinator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio

from ai.dialogue.project_coordinator import ProjectCoordinator

@pytest.fixture
def project_coordinator():
    """Provides a ProjectCoordinator instance with mocked dependencies."""
    mock_llm_interface = AsyncMock()
    mock_service_discovery = AsyncMock()
    mock_hsp_connector = MagicMock()
    mock_agent_manager = MagicMock()
    mock_memory_manager = MagicMock()
    mock_learning_manager = AsyncMock()
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"

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
async def test_handle_project_happy_path(project_coordinator: ProjectCoordinator):
    """Tests the full, successful execution of a project."""
    pc = project_coordinator
    user_query = "Build a website for me."
    decomposed_tasks = [
        {"capability_needed": "create_files_v1", "task_parameters": {"files": ["index.html"]}, "task_description": "Create a homepage."}
    ]
    execution_results = {"0": {"status": "success", "result": "index.html created."}}
    final_integrated_response = "I have successfully created the index.html file for your website."

    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=decomposed_tasks)
    pc._execute_task_graph = AsyncMock(return_value=execution_results)
    pc._integrate_subtask_results = AsyncMock(return_value=final_integrated_response)
    
    available_capabilities = []
    pc.service_discovery.get_all_capabilities_async = AsyncMock(return_value=available_capabilities)

    response = await pc.handle_project(user_query, "session123", "user456")

    pc._decompose_user_intent_into_subtasks.assert_awaited_once_with(user_query, available_capabilities)
    pc._execute_task_graph.assert_awaited_once_with(decomposed_tasks)
    pc._integrate_subtask_results.assert_awaited_once_with(user_query, execution_results)
    pc.learning_manager.learn_from_project_case.assert_awaited_once()

    expected_response = f"TestAI, Here's the result of your project request,\n\n{final_integrated_response}"
    assert response == expected_response

@pytest.mark.asyncio
async def test_handle_project_decomposition_fails(project_coordinator: ProjectCoordinator):
    """Tests that if task decomposition fails, a user-friendly message is returned."""
    pc = project_coordinator
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=[])

    with patch.object(pc, '_execute_task_graph', new_callable=AsyncMock) as mock_execute, \
         patch.object(pc, '_integrate_subtask_results', new_callable=AsyncMock) as mock_integrate:
        response = await pc.handle_project("An impossible task.", "s1", "u1")
        assert response == "TestAI, I couldn't break down your request into a clear plan."
        mock_execute.assert_not_called()
        mock_integrate.assert_not_called()

@pytest.mark.asyncio
async def test_execute_task_graph_with_dependencies(project_coordinator: ProjectCoordinator):
    """Tests that _execute_task_graph correctly handles dependencies between tasks."""
    pc = project_coordinator
    pc._dispatch_single_subtask = AsyncMock(side_effect=[
        {"result": "Task 0 was successful"},
        {"result": "Task 1 was successful"}
    ])

    subtasks = [
        {"capability_needed": "task0_v1", "task_parameters": {"param": "A"}},
        {"capability_needed": "task1_v1", "task_parameters": {"input_data": "Some static data and <output_of_task_0>"}}
    ]

    results = await pc._execute_task_graph(subtasks)

    assert len(results) == 2
    assert results[0] == {"result": "Task 0 was successful"}
    assert results[1] == {"result": "Task 1 was successful"}

    expected_call_for_task1 = call({
        'capability_needed': 'task1_v1',
        'task_parameters': {'input_data': 'Some static data and {\'result\': \'Task 0 was successful\'} '}
    })
    pc._dispatch_single_subtask.assert_has_calls([
        call(subtasks[0]),
        expected_call_for_task1
    ])

@pytest.mark.asyncio
async def test_dispatch_single_subtask_agent_not_found(project_coordinator: ProjectCoordinator):
    """Tests that if an agent cannot be found or launched, an error is returned."""
    pc = project_coordinator
    pc.service_discovery.find_capabilities = AsyncMock(return_value=[])
    pc.agent_manager.launch_agent.return_value = None

    subtask = {"capability_needed": "non_existent_capability_v1"}
    result = await pc._dispatch_single_subtask(subtask)

    assert result == {"error": "Could not find or launch an agent with capability 'non_existent_capability_v1'."}

@pytest.mark.asyncio
async def test_dispatch_single_subtask_agent_launch_and_discovery(project_coordinator: ProjectCoordinator):
    """Tests the logic for launching a new agent when a capability is not initially found."""
    pc = project_coordinator
    capability_name = "needed_capability_v1"
    agent_name_to_launch = "needed_capability_agent"
    subtask = {"capability_needed": capability_name, "task_parameters": {}}

    new_capability_payload = {
        "capability_id": "cap_123",
        "ai_id": "agent_xyz",
    }

    pc.service_discovery.find_capabilities = AsyncMock(side_effect=[
        [],
        [new_capability_payload]
    ])

    mock_future = asyncio.Future()
    mock_future.set_result(True)
    pc.agent_manager.launch_agent.return_value = mock_future

    pc._send_hsp_request = AsyncMock(return_value=("Request sent.", "corr_123"))
    pc._wait_for_task_result = AsyncMock(return_value={"status": "success"})

    result = await pc._dispatch_single_subtask(subtask)

    pc.agent_manager.launch_agent.assert_called_once_with(agent_name_to_launch)

@pytest.mark.asyncio
async def test_wait_for_task_result_timeout(project_coordinator: ProjectCoordinator):
    """Tests that _wait_for_task_result correctly returns an error on timeout."""
    pc = project_coordinator
    pc.turn_timeout_seconds = 0.01
    result = await pc._wait_for_task_result("corr_timeout", "timeout_capability")
    assert result == {"error": "Task for 'timeout_capability' timed out."}
