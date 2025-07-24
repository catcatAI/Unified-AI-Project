import pytest
from unittest.mock import AsyncMock, MagicMock

# Test cases for the ProjectCoordinator using the centralized mock_core_services fixture

@pytest.mark.asyncio
async def test_handle_project_decomposes_and_executes(mock_core_services):
    """
    Tests that handle_project correctly decomposes the user query,
    executes the resulting graph, and integrates the results.
    """
    # Arrange
    pc = mock_core_services["project_coordinator"]
    llm_interface = mock_core_services["llm_interface"]
    service_discovery = mock_core_services["service_discovery"]

    # Mock the responses from the LLM
    llm_interface.generate_response.side_effect = [
        '[{"capability_needed": "test_capability_v1", "task_parameters": {"param": "value"}, "task_description": "Test task"}]',
        "Final integrated response."
    ]

    # Mock the service discovery and task execution
    service_discovery.get_all_capabilities.return_value = []
    pc._execute_task_graph = AsyncMock(return_value={0: {"result": "Subtask result"}})

    # Act
    final_response = await pc.handle_project("Test project", "session1", "user1")

    # Assert
    assert final_response == "TestAI: Here's the result of your project request:\n\nFinal integrated response."
    llm_interface.generate_response.assert_any_call(prompt=pc.prompts['decompose_user_intent'].format(capabilities='[]', user_query='Test project'))
    pc._execute_task_graph.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_task_graph_with_dependencies(mock_core_services):
    """
    Tests that _execute_task_graph correctly handles dependencies between tasks.
    """
    # Arrange
    pc = mock_core_services["project_coordinator"]
    pc._dispatch_single_subtask = AsyncMock(side_effect=[
        {"result": "Task 0 result"},
        {"result": "Task 1 result"}
    ])

    subtasks = [
        {"capability_needed": "task0_v1", "task_parameters": {}},
        {"capability_needed": "task1_v1", "task_parameters": {"input": "<output_of_task_0>"}}
    ]

    # Act
    results = await pc._execute_task_graph(subtasks)

    # Assert
    assert results == {0: {"result": "Task 0 result"}, 1: {"result": "Task 1 result"}}
    # Check that the second task received the output of the first task
    pc._dispatch_single_subtask.assert_any_call({
        'capability_needed': 'task1_v1',
        'task_parameters': {'input': '{"result": "Task 0 result"}'}
    })

@pytest.mark.asyncio
async def test_execute_task_graph_circular_dependency(mock_core_services):
    """
    Tests that _execute_task_graph raises a ValueError for circular dependencies.
    """
    # Arrange
    pc = mock_core_services["project_coordinator"]
    subtasks = [
        {"capability_needed": "task0_v1", "task_parameters": {"input": "<output_of_task_1>"}},
        {"capability_needed": "task1_v1", "task_parameters": {"input": "<output_of_task_0>"}}
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Task 0 has an invalid dependency on a future task 1."):
        await pc._execute_task_graph(subtasks)
